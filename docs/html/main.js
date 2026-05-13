var WIKI = WIKI_BASE || 'https://github.com/ccckmit/course0/blob/main/wiki';
var CODE = CODE_BASE || 'https://github.com/ccckmit/course0/blob/main/code';

var CODE_MAP = {
  '編譯器': ['compiler/py/py1i','compiler/py/py1c'],
  '作業系統': ['os/mini-riscv-os2','os/xv7'],
  '虛擬機': ['irvm/py0/py0i','irvm/qd0/qd0c'],
  '網路': ['network/fastapi0'],
  '直譯器': ['irvm/py0/py0i'],
  'RISC-V': ['os/mini-riscv-os2'],
  'Linux': ['os/xv7'],
  'HTTP': ['network/fastapi0'],
  'C語言': ['compiler/c/c0'],
  'Socket': ['network/drop0box'],
  'Unix': ['os/xv7'],
};

function findCode(name) {
  var keys = Object.keys(CODE_MAP);
  for (var i = 0; i < keys.length; i++) {
    if (name.indexOf(keys[i]) !== -1) {
      var paths = CODE_MAP[keys[i]];
      var links = '';
      for (var j = 0; j < paths.length; j++) {
        links += '<a href="' + CODE + '/' + paths[j] + '">📁 ' + paths[j] + '</a>';
      }
      return links;
    }
  }
  return '';
}

function showCard(item) {
  var h = '<div class="card"><h3>';
  if (item.file) h += '<a href="' + WIKI + '/' + item.file + '">' + item.name + '</a>';
  else h += item.name;
  h += '</h3>';
  if (item.desc) h += '<p>' + item.desc + '</p>';
  var links = findCode(item.name);
  if (links) h += '<div class="links">' + links + '</div>';
  h += '</div>';
  return h;
}

function renderConcept() {
  var html = '';
  var keys = Object.keys(concepts);
  for (var k = 0; k < keys.length; k++) {
    var key = keys[k];
    var items = concepts[key];
    html += '<h2 class="section-title">' + key + '</h2><div class="grid">';
    for (var i = 0; i < items.length; i++) {
      html += showCard(items[i]);
    }
    html += '</div>';
  }
  document.getElementById('content').innerHTML = html;
}

function renderCode() {
  var html = '<h2 class="section-title">💻 程式碼</h2><div class="grid">';
  for (var i = 0; i < codes.length; i++) {
    var c = codes[i];
    html += '<div class="card"><h3>' + c.name + '</h3><div class="links">';
    for (var j = 0; j < c.files.length; j++) {
      html += '<a href="' + CODE + '/' + c.path + '/' + c.files[j] + '">' + c.files[j] + '</a>';
    }
    html += '</div></div>';
  }
  html += '</div>';
  document.getElementById('content').innerHTML = html;
}

function render(tab) {
  if (tab === '概念') renderConcept();
  else renderCode();
}

function doSearch() {
  var q = document.getElementById('search').value.toLowerCase();
  var cards = document.querySelectorAll('.card');
  for (var i = 0; i < cards.length; i++) {
    cards[i].style.display = cards[i].textContent.toLowerCase().indexOf(q) === -1 ? 'none' : '';
  }
}

function initTabs() {
  var tabs = document.querySelectorAll('.tab');
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].onclick = function() {
      for (var j = 0; j < tabs.length; j++) tabs[j].classList.remove('active');
      this.classList.add('active');
      cur = this.getAttribute('data-tab');
      document.getElementById('search').value = '';
      render(cur);
    };
  }
}