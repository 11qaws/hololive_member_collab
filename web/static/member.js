/* HCAT Member Timeline — client-side rendering engine */
(function() {
  'use strict';

  var allEntries = [];
  var filteredEntries = [];
  var renderedCount = 0;
  var BATCH_SIZE = 50;
  var selectedPartners = [];
  var memberPhotos = {};
  var filterTimer = null;

  var container = document.getElementById('timeline-container');
  var countEl = document.getElementById('tl-count');
  var filterInfo = document.getElementById('filterInfo');

  /* ── Utility ── */
  function fuwamocoDisplay(handle, title) {
    var base = (handle || '').toLowerCase().replace('_abyssgard', '');
    if (['fuwawa','mococo','fuwamococh'].indexOf(base) === -1) return handle;
    var tu = (title || '').toUpperCase();
    if (tu.indexOf('POV') !== -1 || tu.indexOf('SOLO') !== -1) {
      if (tu.indexOf('\u3010FUWAWA POV\u3011') !== -1 || tu.indexOf('\u3010FUWAWA SOLO\u3011') !== -1) return 'FUWAmoco';
      if (tu.indexOf('\u3010MOCOCO POV\u3011') !== -1 || tu.indexOf('\u3010MOCOCO SOLO\u3011') !== -1) return 'fuwaMOCO';
      if (handle === 'fuwawa_abyssgard') return 'FUWAmoco';
      if (handle === 'mococo_abyssgard') return 'fuwaMOCO';
    }
    return 'FUWAMOCOch';
  }

  function fmtDate(d) {
    if (!d || d.length < 8) return d;
    return d.slice(0,4) + '-' + d.slice(4,6) + '-' + d.slice(6,8);
  }

  function monthLabel(d) {
    if (!d || d.length < 6) return '';
    return d.slice(0,4) + '\ub144 ' + parseInt(d.slice(4,6), 10) + '\uc6d4';
  }

  function escapeHtml(s) {
    if (!s) return '';
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function subAvatar(handle) {
    var photo = memberPhotos[handle];
    if (photo) return '<img class="sub-avatar" src="' + escapeHtml(photo) + '" alt="">';
    return '<span class="sub-dot"></span>';
  }

  /* ── Entry HTML builders ── */

  function renderStreamEntry(e) {
    var thumb = e.thumbnail || '';
    var ttl = e.title || '';
    return '<div class="tl-item stream" data-date="' + e.published_at + '" data-partners="">' +
      '<div class="tl-dot"></div>' +
      '<div class="tl-card"><a href="' + escapeHtml(e.url) + '" target="_blank">' +
      (thumb ? '<img class="tl-thumb" src="' + escapeHtml(thumb) + '" alt="" loading="lazy">' : '<div class="tl-thumb" style="display:flex;align-items:center;justify-content:center;font-size:1.25rem">\ud83c\udfac</div>') +
      '<div class="tl-body"><div class="tl-title">' + escapeHtml(ttl) + '</div>' +
      '<div class="tl-meta"><span class="tl-badge tl-badge-stream">STREAM</span> ' + fmtDate(e.published_at) + '</div>' +
      '</div></a></div></div>';
  }

  function renderCollabEntry(e) {
    var isGroup = e.sub_entries && e.sub_entries.length > 1;
    var partnerHandle = e.partner_handle || (e.sub_entries && e.sub_entries[0] ? e.sub_entries[0].partner_handle : '') || '';
    var allPartners = e.partner_handle || '';
    if (e.sub_entries) {
      e.sub_entries.forEach(function(se) { allPartners += ' ' + (se.partner_handle || ''); });
    }
    var thumb = e.thumbnail || '';
    var ttl = e.title || '';

    var html = '<div class="tl-item collab" data-date="' + e.published_at + '" data-partners="' + allPartners.trim() + '">' +
      '<div class="tl-dot"></div>' +
      '<div class="tl-card' + (isGroup ? ' collab-group' : '') + '"' + (isGroup ? ' onclick="toggleCollabGroup(this)"' : '') + '>';

    if (isGroup) {
      html += '<div class="tl-card-inner no-link">';
    } else {
      var linkUrl = (e.sub_entries && e.sub_entries[0]) ? e.sub_entries[0].url : e.url;
      html += '<a href="' + escapeHtml(linkUrl) + '" target="_blank">';
    }

    html += (thumb ? '<img class="tl-thumb" src="' + escapeHtml(thumb) + '" alt="" loading="lazy">' : '<div class="tl-thumb" style="display:flex;align-items:center;justify-content:center;font-size:1.25rem">\ud83c\udf99</div>') +
      '<div class="tl-body"><div class="tl-title">' + escapeHtml(ttl) + '</div>' +
      '<div class="tl-meta"><span class="tl-badge tl-badge-collab">COLLAB</span> ' + fmtDate(e.published_at);

    if (!isGroup && partnerHandle) {
      html += ' \u00b7 by @' + fuwamocoDisplay(partnerHandle, ttl);
    }
    html += '</div>';

    if (isGroup) {
      var subCount = e.sub_entries.length;
      html += '<div class="tl-partners"><span class="partner">' + subCount + ' videos</span>';
      for (var i = 0; i < Math.min(3, subCount); i++) {
        html += ' <span class="partner">@' + fuwamocoDisplay(e.sub_entries[i].partner_handle, e.sub_entries[i].title) + '</span>';
      }
      if (subCount > 3) html += ' <span class="partner">+' + (subCount - 3) + ' more</span>';
      html += '<span class="tl-arrow">\u25b6</span></div>';
    }

    html += '</div>';
    if (!isGroup) { html += '</a>'; } else { html += '</div>'; }

    if (isGroup && e.sub_entries) {
      html += '<div class="tl-subs">';
      e.sub_entries.forEach(function(se) {
        html += '<a class="tl-sub" href="' + escapeHtml(se.url) + '" target="_blank">' +
          subAvatar(se.partner_handle) +
          '<div class="tl-sub-title">' + escapeHtml(se.title) + '</div>' +
          '<span class="tl-sub-meta">@' + fuwamocoDisplay(se.partner_handle, se.title) + '</span></a>';
      });
      html += '</div>';
    }

    html += '</div></div>';
    return html;
  }

  function renderPairedEntry(e) {
    var ps = e.paired_self;
    var isGroup = e.sub_entries && e.sub_entries.length > 1;
    var allPartners = e.partner_handle || '';
    if (e.sub_entries) {
      e.sub_entries.forEach(function(se) { allPartners += ' ' + (se.partner_handle || ''); });
    }
    var thumb = e.thumbnail || '';

    var html = '<div class="tl-item pair" data-date="' + e.published_at + '" data-partners="' + allPartners.trim() + '">' +
      '<div class="tl-pair-stream"><a class="tl-card" href="' + escapeHtml(ps.url) + '" target="_blank">' +
      (ps.thumbnail ? '<img class="tl-thumb" src="' + escapeHtml(ps.thumbnail) + '" alt="" loading="lazy">' : '<div class="tl-thumb" style="display:flex;align-items:center;justify-content:center;font-size:1.25rem">\ud83c\udfac</div>') +
      '<div class="tl-body"><div class="tl-title">' + escapeHtml(ps.title) + '</div>' +
      '<div class="tl-meta"><span class="tl-badge tl-badge-stream">STREAM</span> ' + fmtDate(ps.published_at) + '</div>' +
      '</div></a></div>' +
      '<div class="tl-dot"></div>' +
      '<div class="tl-pair-collab"><div class="tl-card' + (isGroup ? ' collab-group' : '') + '"' + (isGroup ? ' onclick="toggleCollabGroup(this)"' : '') + '>';

    if (isGroup) {
      html += '<div class="tl-card-inner no-link">';
    } else {
      var linkUrl = (e.sub_entries && e.sub_entries[0]) ? e.sub_entries[0].url : e.url;
      html += '<a href="' + escapeHtml(linkUrl) + '" target="_blank">';
    }

    html += (thumb ? '<img class="tl-thumb" src="' + escapeHtml(thumb) + '" alt="" loading="lazy">' : '<div class="tl-thumb" style="display:flex;align-items:center;justify-content:center;font-size:1.25rem">\ud83c\udf99</div>') +
      '<div class="tl-body"><div class="tl-title">' + escapeHtml(e.title) + '</div>' +
      '<div class="tl-meta"><span class="tl-badge tl-badge-collab">COLLAB</span> ' + fmtDate(e.published_at);

    if (!isGroup) {
      var ph = e.partner_handle || (e.sub_entries && e.sub_entries[0] ? e.sub_entries[0].partner_handle : '');
      if (ph) html += ' \u00b7 by @' + fuwamocoDisplay(ph, e.title);
    }
    html += '</div>';

    if (isGroup) {
      var subCount = e.sub_entries.length;
      html += '<div class="tl-partners"><span class="partner">' + subCount + ' videos</span><span class="tl-arrow">\u25b6</span></div>';
    }

    html += '</div>';
    if (!isGroup) { html += '</a>'; } else { html += '</div>'; }

    if (isGroup && e.sub_entries) {
      html += '<div class="tl-subs">';
      e.sub_entries.forEach(function(se) {
        html += '<a class="tl-sub" href="' + escapeHtml(se.url) + '" target="_blank">' +
          subAvatar(se.partner_handle) +
          '<div class="tl-sub-title">' + escapeHtml(se.title) + '</div>' +
          '<span class="tl-sub-meta">@' + fuwamocoDisplay(se.partner_handle, se.title) + '</span></a>';
      });
      html += '</div>';
    }

    html += '</div></div></div>';
    return html;
  }

  /* ── Timeline rendering ── */

  function insertMonthDivider(prevMonth, currentMonth) {
    if (!currentMonth) return '';
    if (currentMonth !== prevMonth) {
      return '<div class="tl-month-divider"><span class="tl-month-label">' + monthLabel(currentMonth) + '</span></div>';
    }
    return '';
  }

  function renderBatch(start, count) {
    var html = '';
    var end = Math.min(start + count, filteredEntries.length);
    var prevMonth = (start > 0) ? filteredEntries[start - 1].published_at.slice(0,6) : '';

    for (var i = start; i < end; i++) {
      var e = filteredEntries[i];
      var curMonth = (e.published_at || '').slice(0,6);
      html += insertMonthDivider(prevMonth, curMonth);
      prevMonth = curMonth;

      if (e.entry_type === 'stream') {
        html += renderStreamEntry(e);
      } else if (e.paired_self) {
        html += renderPairedEntry(e);
      } else {
        html += renderCollabEntry(e);
      }
    }

    // Append last month divider if we rendered all entries
    if (end === filteredEntries.length && prevMonth) {
      html += '<div class="tl-month-divider"><span class="tl-month-label">' + monthLabel(prevMonth) + '</span></div>';
    }

    return html;
  }

  var sentinel = null;
  var observer = null;

  function setupObserver() {
    if (observer) observer.disconnect();
    if (renderedCount >= filteredEntries.length) {
      if (sentinel) { sentinel.style.display = 'none'; }
      return;
    }
    if (!sentinel) {
      sentinel = document.createElement('div');
      sentinel.className = 'tl-load-more';
      container.appendChild(sentinel);
    }
    sentinel.style.display = '';
    sentinel.textContent = renderedCount + ' / ' + filteredEntries.length + ' entries loaded';

    observer = new IntersectionObserver(function(entries) {
      if (entries[0].isIntersecting) {
        loadMore();
      }
    }, { rootMargin: '200px' });
    observer.observe(sentinel);
  }

  function loadMore() {
    var batchHtml = renderBatch(renderedCount, BATCH_SIZE);
    renderedCount = Math.min(renderedCount + BATCH_SIZE, filteredEntries.length);
    // Remove sentinel temporarily, append batch, then re-add sentinel
    if (sentinel && sentinel.parentNode) sentinel.remove();
    container.insertAdjacentHTML('beforeend', batchHtml);
    updateCount();
    if (renderedCount < filteredEntries.length) {
      container.appendChild(sentinel);
      sentinel.textContent = renderedCount + ' / ' + filteredEntries.length + ' entries loaded';
      if (observer) observer.observe(sentinel);
    } else {
      if (sentinel) {
        sentinel.textContent = renderedCount + ' entries';
        sentinel.style.display = 'none';
      }
    }
  }

  function renderTimeline() {
    container.innerHTML = '';
    renderedCount = 0;
    if (filteredEntries.length === 0) {
      container.innerHTML = '<div class="tl-empty">No matching entries found.</div>';
      updateCount();
      return;
    }
    // Initial render: first batch
    var batchHtml = renderBatch(0, BATCH_SIZE);
    renderedCount = Math.min(BATCH_SIZE, filteredEntries.length);
    container.innerHTML = batchHtml;
    updateCount();
    setupObserver();
  }

  function updateCount() {
    if (countEl) {
      countEl.textContent = '\u00b7 ' + filteredEntries.length + ' entries';
    }
    if (filterInfo) {
      if (filteredEntries.length < allEntries.length) {
        filterInfo.textContent = 'Showing ' + filteredEntries.length + ' of ' + allEntries.length + ' entries';
      } else {
        filterInfo.textContent = '';
      }
    }
  }

  /* ── Filtering ── */

  function applyFilters() {
    var kw = (document.getElementById('keywordFilter').value || '').toLowerCase();
    var dateFrom = document.getElementById('dateFrom').value || '';
    var dateTo = document.getElementById('dateTo').value || '';
    if (dateFrom) dateFrom = dateFrom.replace(/-/g, '');
    if (dateTo) dateTo = dateTo.replace(/-/g, '');

    filteredEntries = allEntries.filter(function(e) {
      if (kw) {
        var titleMatch = (e.title || '').toLowerCase().indexOf(kw) !== -1;
        if (!titleMatch) return false;
      }
      if (dateFrom && (e.published_at || '') < dateFrom) return false;
      if (dateTo && (e.published_at || '') > dateTo) return false;
      if (selectedPartners.length > 0) {
        var partners = e.partner_handle || '';
        if (e.sub_entries) {
          e.sub_entries.forEach(function(se) { partners += ' ' + (se.partner_handle || ''); });
        }
        var match = selectedPartners.some(function(s) { return partners.indexOf(s) !== -1; });
        if (!match) return false;
      }
      return true;
    });

    renderTimeline();
  }

  function queueFilter() {
    if (filterTimer) clearTimeout(filterTimer);
    filterTimer = setTimeout(applyFilters, 150);
  }

  /* ── Partner filter dropdown ── */

  function buildPartnerDropdown(groups) {
    var dd = document.getElementById('partnerDropdown');
    dd.innerHTML = '';
    groups.forEach(function(g) {
      var branch = g[0];
      var items = g[1];
      var groupDiv = document.createElement('div');
      groupDiv.className = 'partner-group';
      groupDiv.innerHTML = '<div class="partner-group-header" onclick="toggleGroup(this)">' +
        '<span class="pgg-arrow">\u25b6</span>' +
        '<span class="pgg-label">' + escapeHtml(branch) + '</span>' +
        '<span class="pgg-count">' + items.length + '</span></div>' +
        '<div class="partner-group-body">' +
        items.map(function(p) {
          return '<div class="partner-option" data-handle="' + escapeHtml(p.handle) + '" onclick="togglePartnerOption(this)">' +
            '<span class="po-name">' + escapeHtml(p.name) + '</span>' +
            '<span class="po-handle">@' + escapeHtml(p.handle) + '</span></div>';
        }).join('') +
        '</div>';
      dd.appendChild(groupDiv);
    });
    document.getElementById('filter-bar').style.display = '';
  }

  /* ── URL state ── */

  function syncURL() {
    var params = [];
    var kw = document.getElementById('keywordFilter').value;
    if (kw) params.push('q=' + encodeURIComponent(kw));
    var from = document.getElementById('dateFrom').value;
    if (from) params.push('from=' + from);
    var to = document.getElementById('dateTo').value;
    if (to) params.push('to=' + to);
    if (selectedPartners.length > 0) params.push('partner=' + selectedPartners.join(','));
    var url = window.location.pathname;
    if (params.length > 0) url += '?' + params.join('&');
    history.replaceState(null, '', url);
  }

  function readURL() {
    var p = new URLSearchParams(window.location.search);
    var kw = p.get('q');
    if (kw) { document.getElementById('keywordFilter').value = kw; }
    var from = p.get('from');
    if (from) { document.getElementById('dateFrom').value = from; }
    var to = p.get('to');
    if (to) { document.getElementById('dateTo').value = to; }
    var partnerStr = p.get('partner');
    if (partnerStr) {
      selectedPartners = partnerStr.split(',').filter(Boolean);
      selectedPartners.forEach(function(h) {
        var el = document.querySelector('.partner-option[data-handle="' + h + '"]');
        if (el) el.classList.add('selected');
      });
      updateSelectedDisplay();
    }
  }

  /* ── Initialization ── */

  function init() {
    var dataScript = document.getElementById('timeline-data');
    if (!dataScript) return;
    try { allEntries = JSON.parse(dataScript.textContent); } catch(e) { return; }

    var photosScript = document.getElementById('member-photos');
    if (photosScript) {
      try { memberPhotos = JSON.parse(photosScript.textContent); } catch(e) {}
    }

    var groupsScript = document.getElementById('partner-groups');
    if (groupsScript) {
      try {
        var groups = JSON.parse(groupsScript.textContent);
        buildPartnerDropdown(groups);
      } catch(e) {}
    }

    filteredEntries = allEntries.slice();
    readURL();
    applyFilters();
  }

  /* ── Expose to window (for inline onclick handlers) ── */

  window.togglePartnerDropdown = function() {
    document.getElementById('partnerDropdown').classList.toggle('open');
  };

  window.toggleGroup = function(header) {
    var body = header.nextElementSibling;
    var arrow = header.querySelector('.pgg-arrow');
    var isOpen = body.classList.toggle('open');
    arrow.textContent = isOpen ? '\u25bc' : '\u25b6';
  };

  window.togglePartnerOption = function(el) {
    var handle = el.dataset.handle;
    var idx = selectedPartners.indexOf(handle);
    if (idx >= 0) {
      selectedPartners.splice(idx, 1);
      el.classList.remove('selected');
    } else {
      selectedPartners.push(handle);
      el.classList.add('selected');
    }
    updateSelectedDisplay();
    syncURL();
    applyFilters();
  };

  window.updateSelectedDisplay = function() {
    var container = document.getElementById('selectedTags');
    var placeholder = document.getElementById('selectedPlaceholder');
    container.innerHTML = '';
    if (selectedPartners.length === 0) {
      placeholder.style.display = '';
      return;
    }
    placeholder.style.display = 'none';
    selectedPartners.forEach(function(h) {
      var tag = document.createElement('span');
      tag.className = 'selected-tag';
      tag.innerHTML = '@' + h + ' <span class="selected-tag-remove" data-handle="' + h + '">&times;</span>';
      container.appendChild(tag);
    });
    container.querySelectorAll('.selected-tag-remove').forEach(function(btn) {
      btn.onclick = function(e) {
        e.stopPropagation();
        removePartner(this.dataset.handle);
      };
    });
  };

  window.removePartner = function(handle) {
    var idx = selectedPartners.indexOf(handle);
    if (idx >= 0) {
      selectedPartners.splice(idx, 1);
      document.querySelectorAll('.partner-option.selected[data-handle="' + handle + '"]').forEach(function(el) {
        el.classList.remove('selected');
      });
      updateSelectedDisplay();
      syncURL();
      applyFilters();
    }
  };

  window.selectPartnerOnly = function(handle) {
    selectedPartners = [handle];
    document.querySelectorAll('.partner-option').forEach(function(el) {
      el.classList.toggle('selected', el.dataset.handle === handle);
    });
    updateSelectedDisplay();
    syncURL();
    applyFilters();
  };

  window.toggleCollabGroup = function(el) {
    var arrow = el.querySelector('.tl-arrow');
    var subs = el.querySelector('.tl-subs');
    if (subs) {
      subs.classList.toggle('open');
      if (arrow) arrow.classList.toggle('open');
    }
  };

  window.resetFilters = function() {
    document.getElementById('keywordFilter').value = '';
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    selectedPartners = [];
    document.querySelectorAll('.partner-option.selected').forEach(function(el) { el.classList.remove('selected'); });
    updateSelectedDisplay();
    var url = window.location.pathname;
    history.replaceState(null, '', url);
    applyFilters();
  };

  window.queueFilter = function() {
    queueFilter();
    syncURL();
  };

  // Click outside to close partner dropdown
  document.addEventListener('click', function(e) {
    var widget = document.getElementById('partnerSelect');
    if (widget && !widget.contains(e.target)) {
      var dd = document.getElementById('partnerDropdown');
      if (dd) dd.classList.remove('open');
      document.querySelectorAll('.partner-group-body.open').forEach(function(el) { el.classList.remove('open'); });
      document.querySelectorAll('.pgg-arrow').forEach(function(el) { el.textContent = '\u25b6'; });
    }
  });

  // Start
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
