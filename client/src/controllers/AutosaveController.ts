import { Controller } from '@hotwired/stimulus';

import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import { gettext } from '../utils/gettext';
import { debounce, DebouncibleFunction } from '../utils/debounce';

/** Server-provided error codes. */
export enum ServerErrorCode {
  INVALID_REVISION = 'invalid_revision',
  LOCKED = 'locked',
  VALIDATION_ERROR = 'validation_error',
}

/** Server error codes that are generalized as `server_error`. */
export enum UnhandledServerErrorCode {
  BLOCKED_BY_HOOK = 'blocked_by_hook',
  INTERNAL_ERROR = 'internal_error',
}

/** Client-provided error codes. */
export enum ClientErrorCode {
  NETWORK_ERROR = 'network_error',
  SERVER_ERROR = 'server_error',
}

function isHandledServerErrorCode(code: string): code is ServerErrorCode {
  return Object.values(ServerErrorCode).includes(code as ServerErrorCode);
}

export type KnownErrorCode = ServerErrorCode | ClientErrorCode;

/** Error that occurs during hydration of a create view into an edit view. */
export class HydrationError extends Error {
  code: ClientErrorCode;

  constructor(code: ClientErrorCode, ...params: Parameters<ErrorConstructor>) {
    super(...params);
    this.name = 'HydrationError';
    this.code = code;
  }
}

export type AutosaveState = 'idle' | 'saving' | 'saved' | 'paused';

/** Error response from an autosave request. */
export interface AutosaveErrorResponse {
  success: false;
  error_code: ServerErrorCode | UnhandledServerErrorCode;
  error_message: string;
}

/** Successful response from an autosave request. */
export interface AutosaveSuccessResponse {
  success: true;
  pk: number | string;
  revision_id?: number;
  revision_created_at?: string;
  url?: string;
  hydrate_url?: string;
  field_updates?: { [key: string]: string };
  html?: string;
}

export type AutosaveResponse = AutosaveSuccessResponse | AutosaveErrorResponse;

/** The `detail` data for a `w-autosave:save` event. */
export interface AutosaveSaveDetail {
  trigger?: Event;
  formData: FormData;
}

/** The `detail` data for a `w-autosave:hydrate` event. */
export interface AutosaveHydrateDetail {
  trigger?: Event;
  url: string;
}

/** The `detail` data for a `w-autosave:success` event. */
export interface AutosaveSuccessDetail {
  trigger?: Event;
  response: AutosaveSuccessResponse;
  data: AutosaveSuccessResponse;
  timestamp: Date;
}

/** The `detail` data for a `w-autosave:deactivated` event. */
export interface AutosaveDeactivatedDetail {
  trigger?: Event;
  response: AutosaveErrorResponse;
  error: Error;
}

/** The `detail` data for a `w-autosave:error` event. */
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

/**
 * Sends a form's data to the server for autosaving.
 *
 * Can also be used for an indicator component to show the current autosave state.
 *
 * Dispatches the following events.
 *
 * @fires `w-autosave:save` - before saving, cancelable.
 * @fires `w-autosave:hydrate` - to hydrate a create view into an edit view.
 * @fires `w-autosave:success` - on successful save and any UI updates.
 * @fires `w-autosave:deactivated` - when autosave is deactivated due to an unrecoverable error.
 * @fires `w-autosave:error` - on save error, e.g. due to validation errors.
 *
 */
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
  /** The target element for partial HTML updates. */
  declare readonly partialsTarget: HTMLDivElement;

  /**
   * Whether autosave is active.
   *
   * Autosave may be deactivated when there is an unrecoverable error,
   * e.g. a newer revision is detected.
   */
  declare activeValue: boolean;
  /** The debounce interval between autosave calls, in milliseconds. */
  declare intervalValue: number;
  /** The current revision ID of the form being edited. */
  declare revisionIdValue: number;
  /**
   * The current state of the autosave process.
   *
   * This is only set when the controller is used as an indicator component,
   * not when controlling a form.
   */
  declare stateValue: AutosaveState;

  initialize(): void {
    this.submit = this.submit.bind(this);
  }

  /**
   * Prepares a save request by gathering the form data, adding additional data
   * (e.g. revision ID to overwrite), and dispatching a save event.
   *
   * Does not do anything if autosave is not active or the element is not a form.
   */
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

  /**
   * Handles the submission of the autosave form.
   * Debouncible based on the `interval` value.
   *
   * @param event The save event containing the form data to submit.
   * If the event's default is prevented, no action is taken.
   */
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
        throw new Error(response!.error_message || 'Unknown error');
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
        // For create views, we need to swap the form action and the browser URL
        form.action = response.url;
        window.history.replaceState(null, '', response.url);
      }
      if (response.hydrate_url) {
        // and hydrate the create view to turn it into an edit view
        await this.hydrate(
          this.dispatch('hydrate', {
            detail: { url: response.hydrate_url, trigger: event },
          }) as CustomEvent<AutosaveHydrateDetail>,
        );
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
      if (
        !rawResponse ||
        (error instanceof HydrationError &&
          error.code === ClientErrorCode.NETWORK_ERROR)
      ) {
        // Fetch failed, no response at all
        type = ClientErrorCode.NETWORK_ERROR;
        text = gettext('A network error occurred.');
      } else if (
        // Non-JSON response
        !response ||
        // Error during hydration of create view
        (error instanceof HydrationError &&
          error.code === ClientErrorCode.SERVER_ERROR) ||
        // Unknown non-success JSON response (e.g. custom hook response)
        !('error_code' in response) ||
        // Unhandled error code
        !isHandledServerErrorCode(response?.error_code)
      ) {
        type = ClientErrorCode.SERVER_ERROR;
        text = gettext('A server error occurred.');
      } else {
        type = response.error_code as ServerErrorCode;
        text = response.error_message;
      }

      // There's no reliable way to recover from an invalid revision or a
      // hydration error, so deactivate and inform listeners (e.g. to
      // immediately trigger a notification)
      if (
        type === ServerErrorCode.INVALID_REVISION ||
        error instanceof HydrationError
      ) {
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

  /**
   * Fetches the given URL that returns the partials needed to hydrate a create
   * view into an edit view, and put it into the partials target.
   * @param event A CustomEvent containing the URL to fetch.
   */
  async hydrate(event: CustomEvent<AutosaveHydrateDetail>) {
    const { url } = event.detail;

    return fetch(url)
      .catch((error) => {
        throw new HydrationError(
          ClientErrorCode.NETWORK_ERROR,
          'Network error during hydration.',
          { cause: error },
        );
      })
      .then((data) => {
        if (!data.ok)
          throw new HydrationError(
            ClientErrorCode.SERVER_ERROR,
            'Server error during hydration.',
          );
        return data.text();
      })
      .then((html) => {
        if (this.hasPartialsTarget) {
          this.partialsTarget.innerHTML = html;
        }
      })
      .catch((error) => {
        // Rethrow HydrationErrors as it's already handled
        if (error instanceof HydrationError) throw error;

        // Wrap other errors (e.g. if .text() fails)
        throw new HydrationError(
          ClientErrorCode.SERVER_ERROR,
          'Error during hydration.',
          { cause: error },
        );
      });
  }

  /** Applies the new debounce interval to the submit function. */
  intervalValueChanged(newInterval: number) {
    if ('restore' in this.submit) {
      this.submit = this.submit.restore();
    }
    this.submit = debounce(this.submit, newInterval);
  }

  /**
   * Updates the indicator component's state based on events dispatched by the
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
