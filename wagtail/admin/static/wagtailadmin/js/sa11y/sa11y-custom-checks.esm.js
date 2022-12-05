/*-----------------------------------------------------------------------
* Sa11y, the accessibility quality assurance assistant.
* @version: 2.3.5
* @author: Development led by Adam Chaboryk, CPWA
* @acknowledgements: https://this.netlify.app/acknowledgements/
* @license: https://github.com/ryersondmp/sa11y/blob/master/LICENSE.md
* Copyright (c) 2020 - 2022 Toronto Metropolitan University (formerly Ryerson University).
* The above copyright notice shall be included in all copies or
substantial portions of the Software.
------------------------------------------------------------------------*/

class Sa11yCustomChecks {
  setSa11y(sa11y) {
    this.sa11y = sa11y;
  }

  check() {}
}

class CustomChecks extends Sa11yCustomChecks {
  check() {
    /* Note: Strings should match language file. */
    const ERROR = 'Error';
    const WARNING = 'Warning';
    // const GOOD = 'Good';

    /* Add custom rulesets below. */

    /* Custom messages for tooltips. */

    const C = {
      ANNOUNCEMENT_MESSAGE:
        'More than one Announcement component found! The Announcement component should be used strategically and sparingly. It should be used to get attention or indicate that something is important. Misuse of this component makes it less effective or impactful. Secondly, this component is semantically labeled as an Announcement for people who use screen readers.',

      ACCORDION_FORM_MESSAGE:
        'Do <strong>not nest forms</strong> within the Accordion component. If the form contains validation issues, a person may not see the form feedback since the accordion panel goes back to its original closed state.',
    };

    /* Example #1 */
    const $checkAnnouncement = document.querySelectorAll('.sa11y-announcement-component');
    if ($checkAnnouncement.length > 1) {
      for (let i = 1; i < $checkAnnouncement.length; i++) {
        $checkAnnouncement[i].classList.add('sa11y-warning-border');
        $checkAnnouncement[i].insertAdjacentHTML('beforebegin', this.sa11y.annotate(WARNING, C.ANNOUNCEMENT_MESSAGE));
      }
    }

    /* Example #2  */
    const $checkAccordions = this.sa11y.root.querySelectorAll('.sa11y-accordion-example');
    $checkAccordions.forEach(($el) => {
      const checkForm = $el.querySelector('form');
      if (!!checkForm && checkForm.length) {
        $el.classList.add('sa11y-error-border');
        $el.insertAdjacentHTML('beforebegin', this.sa11y.annotate(ERROR, C.ACCORDION_FORM_MESSAGE));
      }
    });

    /* End of custom rulesets.  */
  }
}

export { CustomChecks as default };
