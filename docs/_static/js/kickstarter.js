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
    '<img src="_static/images/kickstarter.png" width="63" height="45" />' +
    '  <span>to accelerate the development of this project.</span>' +
    '</a>');

  if (!hasCookie('kickstarterClosed', 'true')
      && new Date() < new Date(2018, 4, 17)) {
    $('body').prepend($kickstarter);
    $kickstarter.find('.close').click(function (e) {
      e.preventDefault();
      setCookie('kickstarterClosed', 'true', 30);
      $kickstarter.detach();
    });
  }
});
