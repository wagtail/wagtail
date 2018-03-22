function setCookie(name, value, days) {
  const date = new Date();
  date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
  document.cookie = encodeURIComponent(name) + '=' +
                    encodeURIComponent(value) +
                    '; expires=' + date.toGMTString();
}

function hasCookie(name, value) {
  return document.cookie.split('; ').indexOf(name + '=' + value) >= 0;
}

$(function () {
  const $kickstarter = $(
    '<style>' +
    '  a.kickstarter {' +
    '    display: block; width: 100vw; text-align: center;' +
    '    background: #609FD2; color: white; padding: 15px; z-index: 1000;' +
    '  }' +
    '  .kickstarter img {' +
    '    display: inline-block; margin-left: 15px; margin-right: 15px;' +
    '  }' +
    '  .kickstarter .close {' +
    '    float: right; width: 40px; height: 45px; padding: 10px;' +
    '    line-height: 25px; font-size: 20px; font-weight: bold;' +
    '    cursor: pointer;' +
    '  }' +
    '  @media (max-width: 1000px) {' +
    '    .kickstarter span {' +
    '      display: block;' +
    '    }' +
    '    .kickstarter img {' +
    '      display: none;' +
    '    }' +
    '  }' +
    '  @media (min-width: 769px) {' +
    '    .kickstarter {' +
    '      position: fixed;' +
    '    }' +
    '    .wy-nav-side {' +
    '      padding-top: 78px;' +
    '    }' +
    '    .wy-nav-content-wrap {' +
    '      padding-top: 78px;' +
    '    }' +
    '  }' +
    '  @media (min-width: 1000px) {' +
    '    .wy-nav-side {' +
    '      padding-top: 75px;' +
    '    }' +
    '    .wy-nav-content-wrap {' +
    '      padding-top: 75px;' +
    '    }' +
    '  }' +
    '</style>' +
    '<a href="https://www.kickstarter.com/projects/noripyt/wagtails-first-hatch" class="kickstarter">' +
    '  <span class="close">×</span>' +
    '  <span>Please consider supporting ' +
    '    <strong>NoriPyt’s Wagtail Kickstarter</strong>' +
    '  </span>' +
    '  <img alt="" width="63" height="45" src="data:image/png;base64,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" />' +
    '  <span>to accelerate the development of this project.</span>' +
    '</a>');

  if (!hasCookie('kickstarterClosed', 'true')
      && new Date() < new Date(2018, 3, 17)) {
    $('body').prepend($kickstarter);
    $kickstarter.find('.close').click(function (e) {
      e.preventDefault();
      setCookie('kickstarterClosed', 'true', 30);
      $kickstarter.detach();
    });
  }
});
