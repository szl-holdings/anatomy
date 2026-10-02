import importlib.util
import fnmatch
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path); result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
publisher=module('cosmos_publisher',ROOT/'scripts/sync_cosmos.py')
binding=module('cosmos_binding',ROOT/'spaces/cosmos/source_binding.py')

class CosmosPublisherTests(unittest.TestCase):
    def payload(self):
        raw={p.relative_to(ROOT/'spaces/cosmos').as_posix():p.read_bytes() for p in (ROOT/'spaces/cosmos').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        with patch.object(publisher,'source_files',return_value=raw): return publisher.publication_files('a'*40)
    def stage(self, directory):
        files=self.payload()
        for name,data in files.items():
            p=Path(directory)/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        return files
    def test_binding_verifies_every_imported_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.stage(tmp);source,state=binding.bound_source(tmp)
            self.assertEqual(state,'SOURCE_BOUND_LOCAL_BYTES');self.assertEqual(source['commit'],'a'*40)
    def test_tampered_vendor_rejects_source_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.stage(tmp);(Path(tmp)/'vendor/three.module.min.js').write_text('changed')
            self.assertIsNone(binding.bound_source(tmp)[0])
    def test_extra_mounted_html_rejects_source_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.stage(tmp);(Path(tmp)/'unbound.html').write_text('extra')
            self.assertIsNone(binding.bound_source(tmp)[0])
    def test_git_metadata_is_rejected_and_docker_context_excludes_it(self):
        # Model only the simple checked-in ignore patterns; no container claim.
        with tempfile.TemporaryDirectory() as tmp:
            self.stage(tmp);root=Path(tmp);(root/'.git').mkdir();(root/'.git/config').write_text('metadata')
            self.assertIsNone(binding.bound_source(tmp)[0])
            patterns=(ROOT/'spaces/cosmos/.dockerignore').read_text().splitlines()
            def ignored(name):
                parts=Path(name).parts
                prefixes=['/'.join(parts[:i]) for i in range(1,len(parts)+1)]
                return any(fnmatch.fnmatchcase(prefix,pattern) for prefix in prefixes for pattern in patterns)
            for name in ['.git/config','vendor/.git/config','__pycache__/server.cpython-311.pyc','tests/__pycache__/test.pyc','loose.pyc']:
                self.assertTrue(ignored(name),name)
            self.assertFalse(ignored('Dockerfile'))
            self.assertFalse(ignored('.dockerignore'))
            (root/'.git/config').unlink();(root/'.git').rmdir()
            self.assertEqual(binding.bound_source(tmp)[1],'SOURCE_BOUND_LOCAL_BYTES')
    def test_root_dockerignore_allowed_but_nested_hidden_path_rejected(self):
        row=b'100644 blob '+b'a'*40+b'\tspaces/cosmos/.dockerignore\0'
        with patch.object(publisher,'git',side_effect=[row,b'.git\n']):
            with self.assertRaisesRegex(ValueError,'incomplete'):publisher.source_files('b'*40)
        with patch.object(publisher,'git',return_value=b'100644 blob '+b'a'*40+b'\tspaces/cosmos/.dockerignore/secret\0'):
            with self.assertRaisesRegex(ValueError,'unintended'):publisher.source_files('b'*40)
    def test_removed_mounted_file_rejects_source_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.stage(tmp);(Path(tmp)/'NOTICE').unlink()
            self.assertIsNone(binding.bound_source(tmp)[0])
    def test_only_declared_module_bytecode_is_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.stage(tmp);cache=Path(tmp)/'__pycache__';cache.mkdir()
            (cache/'server.cpython-311.pyc').write_bytes(b'runtime cache')
            self.assertEqual(binding.bound_source(tmp)[1],'SOURCE_BOUND_LOCAL_BYTES')
            (cache/'unknown.cpython-311.pyc').write_bytes(b'unbound module')
            self.assertIsNone(binding.bound_source(tmp)[0])
    def test_html_in_bytecode_directory_is_not_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.stage(tmp);cache=Path(tmp)/'__pycache__';cache.mkdir()
            (cache/'unbound.html').write_text('extra')
            self.assertIsNone(binding.bound_source(tmp)[0])
    def test_symlink_directory_rejects_source_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.stage(tmp)
            with patch.object(Path,'is_symlink',lambda path:path.name=='vendor'):
                self.assertIsNone(binding.bound_source(tmp)[0])
    def test_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.stage(tmp);p=Path(tmp)/'COSMOS_SOURCE_BINDING.json';b=json.loads(p.read_text());b['files']['../outside']='0'*64;p.write_text(json.dumps(b))
            self.assertIsNone(binding.bound_source(tmp)[0])
    def test_missing_binding_remains_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:self.assertEqual(binding.bound_source(tmp),(None,'UNKNOWN_SOURCE_RELATION'))
    def test_generated_manifest_replaces_archived_declaration(self):
        m=json.loads(self.payload()['hf-deploy-manifest.json']);self.assertEqual(m['source_repository'],'szl-holdings/anatomy');self.assertEqual(m['source_path'],'spaces/cosmos')
    def test_non_regular_git_entry_rejected(self):
        with patch.object(publisher,'git',return_value=b'120000 blob '+b'a'*40+b'\tspaces/cosmos/link\0'):
            with self.assertRaises(ValueError):publisher.source_files('b'*40)
    def test_extra_remote_output_is_rejected(self):
        class Api:
            def list_repo_files(self,*a,**k):return ['secret.txt']
        with self.assertRaises(RuntimeError):publisher.verify_files(Api(),'b'*40,{},lambda *a:b'')
    def test_different_bytes_are_rejected(self):
        class Api:
            def list_repo_files(self,*a,**k):return ['index.html']
        with self.assertRaises(RuntimeError):publisher.verify_files(Api(),'b'*40,{'index.html':b'a'},lambda *a:b'b')
    def test_hub_revision_cannot_substitute_runtime_revision(self):
        class Info:runtime={'stage':'RUNNING'}
        class Api:
            def space_info(self,*a):return Info()
        with self.assertRaisesRegex(RuntimeError,'runtime revision'):publisher.verify_runtime(Api(),'b'*40,'a'*40)
    def test_dotfile_directory_cannot_bypass_source_filter(self):
        with patch.object(publisher, 'git', return_value=b'100644 blob '+b'a'*40+b'\tspaces/cosmos/.gitattributes/secret\0'):
            with self.assertRaisesRegex(ValueError, 'unintended'): publisher.source_files('b'*40)
    def test_generated_binding_cannot_be_checked_in_as_source(self):
        with patch.object(publisher, 'source_files', return_value={'COSMOS_SOURCE_BINDING.json': b'{}'}):
            with self.assertRaisesRegex(ValueError, 'generated binding'): publisher.publication_files('a'*40)
    def test_identical_publication_has_no_changes(self):
        class Api:
            def list_repo_files(self,*a,**k): return ['index.html']
        self.assertEqual(publisher.changed_files(Api(),'b'*40,{'index.html':b'a'},lambda *a:b'a'), {})
    def test_only_changed_and_missing_files_are_uploaded(self):
        class Api:
            def list_repo_files(self,*a,**k): return ['index.html','server.py']
        expected={'index.html':b'new','server.py':b'same','new.txt':b'added'}
        self.assertEqual(publisher.changed_files(Api(),'b'*40,expected,lambda r,n,s: b'old' if n=='index.html' else b'same'), {'index.html':b'new','new.txt':b'added'})
    def test_binding_noncanonical_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.stage(tmp);p=Path(tmp)/'COSMOS_SOURCE_BINDING.json';b=json.loads(p.read_text());b['files']['./server.py']=b['files']['server.py'];p.write_text(json.dumps(b))
            self.assertIsNone(binding.bound_source(tmp)[0])
    def test_running_stage_is_required(self):
        class Info: runtime={'sha':'b'*40,'stage':'BUILDING'}
        class Api:
            def space_info(self,*a): return Info()
        with self.assertRaisesRegex(RuntimeError, 'runtime revision'): publisher.verify_runtime(Api(),'b'*40,'a'*40)
    def test_six_duplicate_streams_are_rejected(self):
        class Info: runtime={'sha':'b'*40,'stage':'RUNNING'}
        class Api:
            def space_info(self,*a): return Info()
        responses=[{'alignment_state':'SOURCE_BOUND_LOCAL_BYTES','source':{'commit':'a'*40,'repository':publisher.REPOSITORY}}, {'ok':True}, {'state':'FRESH','sources':[{'owner':'SZLHOLDINGS','kind':'space','state':'FRESH'}]*6}]
        with patch.object(publisher,'json_get',side_effect=responses):
            with self.assertRaisesRegex(RuntimeError,'streams'): publisher.verify_runtime(Api(),'b'*40,'a'*40)
    def test_main_movement_between_reads_is_rejected(self):
        responses=[{'archived':False,'default_branch':'main'}, {'protected':True,'commit':{'sha':'a'*40}}, {'sha':'b'*40,'commit':{'verification':{'verified':True}}}]
        with patch.object(publisher,'json_get',side_effect=responses):
            with self.assertRaisesRegex(RuntimeError,'moved'): publisher.main_head('unused')
    def test_comparison_rejects_unowned_remote_files(self):
        class Api:
            def list_repo_files(self,*a,**k): return ['unexpected.txt']
        with self.assertRaisesRegex(RuntimeError,'unowned'):
            publisher.changed_files(Api(),'b'*40,{},lambda *a:b'')

if __name__=='__main__':unittest.main()
