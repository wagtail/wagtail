import { Controller } from '@hotwired/stimulus';

import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import { gettext } from '../utils/gettext';

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
  static values = {
    active: { type: Boolean, default: true },
    revisionId: { type: Number, default: 0 },
    state: { type: String, default: 'idle' as AutosaveState },
  };

  declare activeValue: boolean;
  declare revisionIdValue: number;
  declare stateValue: AutosaveState;

  async submit(event?: Event) {
    if (!this.activeValue || !(this.element instanceof HTMLFormElement)) return;
    const formData = new FormData(this.element);
    if (this.revisionIdValue) {
      formData.set('overwrite_revision_id', `${this.revisionIdValue}`);
    }

    const saveEvent = this.dispatch('save', {
      cancelable: true,
      detail: { formData, trigger: event },
    });
    if (saveEvent.defaultPrevented) return;

    const requestInit: RequestInit = {
      method: this.element.method,
      body: formData,
      headers: {
        Accept: 'application/json',
        [WAGTAIL_CONFIG.CSRF_HEADER_NAME]: WAGTAIL_CONFIG.CSRF_TOKEN,
      },
    };

    let rawResponse: Response | null = null;
    let response: AutosaveResponse | null = null;

    try {
      rawResponse = await fetch(this.element.action, requestInit);
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
          const field = this.element.elements.namedItem(fieldName) as
            | HTMLInputElement
            | HTMLTextAreaElement
            | null;
          if (field) {
            field.value = fieldValue;
          }
        }
      }
      if (response.url) {
        this.element.action = response.url;
      }

      this.dispatch('success', {
        cancelable: false,
        detail: {
          response,
          data: response,
          trigger: event,
        },
      });
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
