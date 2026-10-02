// Display only the immutable identity validated by the same-origin source route.
(function () {
  'use strict';
  var link = document.getElementById('fw-source');
  var revision = document.getElementById('fw-rev');
  var command = document.getElementById('fw-source-command');
  function unavailable() {
    link.removeAttribute('href');
    link.textContent = 'UNKNOWN_SOURCE_RELATION';
    revision.textContent = '';
    command.textContent = 'Unavailable until the mounted source binding is validated.';
  }
  unavailable();
  fetch('/.well-known/szl-source.json', {cache: 'no-store'})
    .then(function (response) {
      if (!response.ok) throw new Error('source endpoint unavailable');
      return response.json();
    })
    .then(function (payload) {
      var source = payload && payload.source;
      if (payload.alignment_state !== 'SOURCE_BOUND_LOCAL_BYTES' || !source ||
          source.repository !== 'szl-holdings/anatomy' || source.path !== 'spaces/cosmos' ||
          typeof source.commit !== 'string' || !/^[0-9a-f]{40}$/.test(source.commit)) {
        unavailable();
        return;
      }
      link.href = 'https://github.com/szl-holdings/anatomy/tree/' + source.commit + '/spaces/cosmos';
      link.textContent = 'szl-holdings/anatomy · spaces/cosmos';
      revision.textContent = ' (source commit ' + source.commit + '; mounted bytes match unsigned binding)';
      command.textContent = 'curl -fsSL https://raw.githubusercontent.com/szl-holdings/anatomy/' + source.commit + '/spaces/cosmos/index.html | sha256sum';
    })
    .catch(unavailable);
})();
