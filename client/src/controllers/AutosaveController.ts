import { Controller } from '@hotwired/stimulus';

import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import { gettext } from '../utils/gettext';
import { debounce, DebouncibleFunction } from '../utils/debounce';

enum ServerErrorCode {
  INVALID_REVISION = 'invalid_revision',
  LOCKED = 'locked',
  VALIDATION_ERROR = 'validation_error',
}

/** Server error codes that are generalized as `server_error`. */
enum UnhandledServerErrorCode {
  BLOCKED_BY_HOOK = 'blocked_by_hook',
  INTERNAL_ERROR = 'internal_error',
}

enum ClientErrorCode {
  NETWORK_ERROR = 'network_error',
  SERVER_ERROR = 'server_error',
}

function isHandledServerErrorCode(code: string): code is ServerErrorCode {
  return Object.values(ServerErrorCode).includes(code as ServerErrorCode);
}

export type KnownErrorCode = ServerErrorCode | ClientErrorCode;

export type AutosaveState = 'idle' | 'saving' | 'saved' | 'paused';

export interface AutosaveErrorResponse {
  success: false;
  errorCode: ServerErrorCode | UnhandledServerErrorCode;
  errorMessage: string;
}

export interface AutosaveSuccessResponse {
  success: true;
  pk: number | string;
  revision_id?: number;
  revision_created_at?: string;
  url?: string;
  field_updates?: { [key: string]: string };
  html?: string;
}

export type AutosaveResponse = AutosaveSuccessResponse | AutosaveErrorResponse;

export interface AutosaveSaveDetail {
  trigger?: Event;
  formData: FormData;
}

export interface AutosaveSuccessDetail {
  trigger?: Event;
  response: AutosaveSuccessResponse;
  data: AutosaveSuccessResponse;
  timestamp: Date;
}

export interface AutosaveDeactivatedDetail {
  trigger?: Event;
  response: AutosaveErrorResponse;
  error: Error;
}

export interface AutosaveErrorDetail {
  trigger?: Event;
  response?: AutosaveErrorResponse | null;
  error: any;
  type: KnownErrorCode;
  text: string;
}

export type AutosaveEvent =
  | CustomEvent<AutosaveSaveDetail>
  | CustomEvent<AutosaveSuccessDetail>
  | CustomEvent<AutosaveDeactivatedDetail>
  | CustomEvent<AutosaveErrorDetail>;

export class AutosaveController extends Controller<
  HTMLFormElement | HTMLDivElement
> {
  static targets = ['partials'];
  static values = {
    active: { type: Boolean, default: true },
    interval: { type: Number, default: 500 },
    revisionId: { type: Number, default: 0 },
    state: { type: String, default: 'idle' as AutosaveState },
  };

  declare readonly hasPartialsTarget: boolean;
  declare readonly partialsTarget: HTMLTemplateElement;

  declare activeValue: boolean;
  declare intervalValue: number;
  declare revisionIdValue: number;
  declare stateValue: AutosaveState;

  initialize(): void {
    this.submit = this.submit.bind(this);
  }

  async save(event?: Event) {
    if (!this.activeValue || !(this.element instanceof HTMLFormElement)) return;
    const formData = new FormData(this.element);
    if (this.revisionIdValue) {
      formData.set('overwrite_revision_id', `${this.revisionIdValue}`);
    }

    this.submit(
      this.dispatch('save', {
        cancelable: true,
        detail: { formData, trigger: event },
      }) as CustomEvent<AutosaveSaveDetail>,
    );
  }

  submit: DebouncibleFunction<
    (event: CustomEvent<AutosaveSaveDetail>) => Promise<void>
  > = async ({ defaultPrevented, detail: { formData, trigger: event } }) => {
    if (defaultPrevented) return;
    const form = this.element as HTMLFormElement;
    const requestInit: RequestInit = {
      method: form.method,
      body: formData,
      headers: {
        Accept: 'application/json',
        [WAGTAIL_CONFIG.CSRF_HEADER_NAME]: WAGTAIL_CONFIG.CSRF_TOKEN,
      },
    };

    let rawResponse: Response | null = null;
    let response: AutosaveResponse | null = null;

    try {
      rawResponse = await fetch(form.action, requestInit);
      response = (await rawResponse.json()) as AutosaveResponse;

      // If we reach here, response must be JSON, but can be of any shape
      if (!response.success) {
        throw new Error(response!.errorMessage || 'Unknown error');
      }

      if (response.revision_id) {
        this.revisionIdValue = response.revision_id;
      }
      if (response.field_updates) {
        for (const [fieldName, fieldValue] of Object.entries(
          response.field_updates,
        )) {
          const field = form.elements.namedItem(fieldName) as
            | HTMLInputElement
            | HTMLTextAreaElement
            | null;
          if (field) {
            field.value = fieldValue;
          }
        }
      }
      if (response.url) {
        form.action = response.url;
      }
      if (this.hasPartialsTarget && response.html) {
        this.partialsTarget.innerHTML = response.html;
      }

      // Ensure any UI updates have finished before dispatching the success event
      requestAnimationFrame(() =>
        this.dispatch('success', {
          cancelable: false,
          detail: {
            response,
            data: response,
            trigger: event,
          },
        }),
      );
    } catch (error) {
      let type: KnownErrorCode;
      let text: string;
      if (!rawResponse) {
        // Fetch failed, no response at all
        type = ClientErrorCode.NETWORK_ERROR;
        text = gettext('A network error occurred.');
      } else if (
        // Non-JSON response
        !response ||
        // Unknown non-success JSON response (e.g. custom hook response)
        !('errorCode' in response) ||
        // Unhandled error code
        !isHandledServerErrorCode(response?.errorCode)
      ) {
        type = ClientErrorCode.SERVER_ERROR;
        text = gettext('A server error occurred.');
      } else {
        type = response.errorCode as ServerErrorCode;
        text = response.errorMessage;
      }

      // There's no way to recover from an invalid revision, so deactivate and
      // inform listeners (e.g. to immediately trigger a notification)
      if (type === ServerErrorCode.INVALID_REVISION) {
        this.activeValue = false;
        this.dispatch('deactivated', {
          cancelable: false,
          detail: {
            response,
            error,
            trigger: event,
          },
        });
      }

      this.dispatch('error', {
        cancelable: false,
        detail: {
          response,
          error,
          trigger: event,
          text, // Used for showing the unsaved changes message
          type,
        },
      });
    }
  };

  intervalValueChanged(newInterval: number) {
    if ('restore' in this.submit) {
      this.submit = this.submit.restore();
    }
    this.submit = debounce(this.submit, newInterval);
  }

  /**
   * Update the indicator component's state based on events dispatched by the
   * controller from the editor form.
   */
  updateIndicator(event: AutosaveEvent) {
    let content = '';

    switch (event.type) {
      case `${this.identifier}:save`:
        this.stateValue = 'saving';
        content = gettext('Autosave in progress…');
        break;
      case `${this.identifier}:success`:
        this.stateValue = 'saved';
        content = gettext('Changes have been autosaved.');
        break;
      case `${this.identifier}:error`:
        this.stateValue = 'paused';
        content = (event as CustomEvent<AutosaveErrorDetail>).detail.text;
        break;
      default:
        this.stateValue = 'idle';
    }

    this.element.setAttribute('data-w-tooltip-content-value', content);
  }
}
