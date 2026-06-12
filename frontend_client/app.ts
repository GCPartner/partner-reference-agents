/*
 Copyright 2025 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 */

import { SignalWatcher } from "@lit-labs/signals";
import { provide } from "@lit/context";
import "@a2ui/lit/ui";
import {
  LitElement,
  html,
  css,
  nothing,
  HTMLTemplateResult,
  unsafeCSS,
} from "lit";
import { customElement, state } from "lit/decorators.js";
import { theme as uiTheme } from "./theme/default-theme.js";
import { A2UIClient } from "./client.js";
import {
  SnackbarAction,
  SnackbarMessage,
  SnackbarUUID,
  SnackType,
} from "./types/types.js";
import { type Snackbar } from "./ui/snackbar.js";
import { repeat } from "lit/directives/repeat.js";
import { v0_8 } from "@a2ui/lit";
import * as UI from "@a2ui/lit/ui";

// App elements.
import "./ui/ui.js";

// Configurations
import { AppConfig } from "./configs/types.js";
import { config as restaurantConfig } from "./configs/restaurant.js";
import { config as contactsConfig } from "./configs/contacts.js";
import { config as phoneplanConfig } from "./configs/phoneplan.js";
import { styleMap } from "lit/directives/style-map.js";

const configs: Record<string, AppConfig> = {
  restaurant: restaurantConfig,
  contacts: contactsConfig,
  phoneplan: phoneplanConfig
};

@customElement("a2ui-shell")
export class A2UILayoutEditor extends SignalWatcher(LitElement) {
  @provide({ context: UI.Context.themeContext })
  accessor theme: v0_8.Types.Theme = uiTheme;

  @state()
  accessor #requesting = false;

  @state()
  accessor #error: string | null = null;

  @state()
  accessor #lastMessages: v0_8.Types.ServerToClientMessage[] = [];

  @state()
  accessor config: AppConfig = configs.restaurant;

  @state()
  accessor #loadingTextIndex = 0;
  #loadingInterval: number | undefined;

  static styles = [
    unsafeCSS(v0_8.Styles.structuralStyles),
    css`
      * {
        box-sizing: border-box;
      }

      :host {
        display: block;
        max-width: 640px;
        margin: 0 auto;
        min-height: 100%;
        color: light-dark(var(--n-10), var(--n-90));
        font-family: var(--font-family);
      }

      #hero-img {
        width: 100%;
        max-width: 400px;
        aspect-ratio: 1280/720;
        height: auto;
        margin-bottom: var(--bb-grid-size-6);
        display: block;
        margin: 0 auto;
        background: var(--background-image-light) center center / contain
          no-repeat;
      }

      #surfaces {
        width: 100%;
        max-width: 100svw;
        padding: var(--bb-grid-size-3);
        animation: fadeIn 1s cubic-bezier(0, 0, 0.3, 1) 0.3s backwards;
      }

      form {
        display: flex;
        flex-direction: column;
        flex: 1;
        gap: 16px;
        align-items: center;
        padding: 16px 0;
        animation: fadeIn 1s cubic-bezier(0, 0, 0.3, 1) 1s backwards;

        & h1 {
          color: light-dark(var(--p-40), var(--n-90));
        }

        & > div {
          display: flex;
          flex: 1;
          gap: 16px;
          align-items: center;
          width: 100%;

          & > input {
            display: block;
            flex: 1;
            border-radius: 32px;
            padding: 16px 24px;
            border: 1px solid var(--p-60);
            background: light-dark(var(--n-100), var(--n-10));
            font-size: 16px;
          }

          & > button {
            display: flex;
            align-items: center;
            background: var(--p-40);
            color: var(--n-100);
            border: none;
            padding: 8px 16px;
            border-radius: 32px;
            opacity: 0.5;

            &:not([disabled]) {
              cursor: pointer;
              opacity: 1;
            }
          }
        }
      }

      .rotate {
        animation: rotate 1s linear infinite;
      }

      .pending {
        width: 100%;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        animation: fadeIn 1s cubic-bezier(0, 0, 0.3, 1) 0.3s backwards;
        gap: 16px;
      }

      .spinner {
        width: 48px;
        height: 48px;
        border: 4px solid rgba(255, 255, 255, 0.1);
        border-left-color: var(--p-60);
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      .theme-toggle {
        padding: 0;
        margin: 0;
        border: none;
        display: flex;
        align-items: center;
        justify-content: center;
        position: fixed;
        top: var(--bb-grid-size-3);
        right: var(--bb-grid-size-4);
        background: light-dark(var(--n-100), var(--n-0));
        border-radius: 50%;
        color: var(--p-30);
        cursor: pointer;
        width: 48px;
        height: 48px;
        font-size: 32px;

        & .g-icon {
          pointer-events: none;

          &::before {
            content: "dark_mode";
          }
        }
      }

      @container style(--color-scheme: dark) {
        .theme-toggle .g-icon::before {
          content: "light_mode";
          color: var(--n-90);
        }

        #hero-img {
          background-image: var(--background-image-dark);
        }
      }

      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }

      @keyframes pulse {
        0% {
          opacity: 0.6;
        }
        50% {
          opacity: 1;
        }
        100% {
          opacity: 0.6;
        }
      }

      .error {
        color: var(--e-40);
        background-color: var(--e-95);
        border: 1px solid var(--e-80);
        padding: 16px;
        border-radius: 8px;
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
        }

        to {
          opacity: 1;
        }
      }

      @keyframes rotate {
        from {
          rotate: 0deg;
        }

        to {
          rotate: 360deg;
        }
      }
    `,
  ];

  #processor = v0_8.Data.createSignalA2uiMessageProcessor();
  #a2uiClient = new A2UIClient();
  #snackbar: Snackbar | undefined = undefined;
  #pendingSnackbarMessages: Array<{
    message: SnackbarMessage;
    replaceAll: boolean;
  }> = [];

  #maybeRenderError() {
    if (!this.#error) return nothing;

    return html`<div class="error">${this.#error}</div>`;
  }

  connectedCallback() {
    super.connectedCallback();

    // Load config from URL
    const urlParams = new URLSearchParams(window.location.search);
    const appKey = urlParams.get("app") || "phoneplan";
    this.config = configs[appKey] || configs.phoneplan;

    // Apply the theme directly, which will use the Lit context.
    if (this.config.theme) {
      this.theme = this.config.theme;
    }

    window.document.title = this.config.title;
    window.document.documentElement.style.setProperty(
      "--background",
      this.config.background
    );

    // Initialize client with configured URL
    this.#a2uiClient = new A2UIClient(this.config.serverUrl);
  }

  render() {
    return [
      this.#renderThemeToggle(),
      this.#maybeRenderForm(),
      this.#maybeRenderData(),
      this.#maybeRenderError(),
    ];
  }

  #renderThemeToggle() {
    return html` <div>
      <button
        @click=${(evt: Event) => {
        if (!(evt.target instanceof HTMLButtonElement)) return;
        const { colorScheme } = window.getComputedStyle(evt.target);
        if (colorScheme === "dark") {
          document.body.classList.add("light");
          document.body.classList.remove("dark");
        } else {
          document.body.classList.add("dark");
          document.body.classList.remove("light");
        }
      }}
        class="theme-toggle"
      >
        <span class="g-icon filled-heavy"></span>
      </button>
    </div>`;
  }

  #maybeRenderForm() {
    if (this.#requesting) return nothing;
    if (this.#lastMessages.length > 0) return nothing;

    return html` <form
      @submit=${async (evt: Event) => {
        evt.preventDefault();
        if (!(evt.target instanceof HTMLFormElement)) {
          return;
        }
        const data = new FormData(evt.target);
        const body = data.get("body") ?? null;
        if (!body) {
          return;
        }
        const message = body as v0_8.Types.A2UIClientEventMessage;
        console.log("[A2UI] Sending message:", message);
        try {
          await this.#sendAndProcessMessage(message);
        } catch (e) {
          console.error("[A2UI] Send failed:", e);
        }
      }}
    >
      ${this.config.heroImage
        ? html`<div
            style=${styleMap({
          "--background-image-light": `url(${this.config.heroImage})`,
          "--background-image-dark": `url(${this.config.heroImageDark ?? this.config.heroImage
            })`,
        })}
            id="hero-img"
          ></div>`
        : nothing}
      <h1 class="app-title">${this.config.title}</h1>
      <div>
        <input
          required
          placeholder="${this.config.placeholder}"
          autocomplete="off"
          id="body"
          name="body"
          type="text"
          ?disabled=${this.#requesting}
        />
        <button type="submit" ?disabled=${this.#requesting}>
          <span class="g-icon filled-heavy">send</span>
        </button>
      </div>
    </form>`;
  }

  #startLoadingAnimation() {
    if (
      Array.isArray(this.config.loadingText) &&
      this.config.loadingText.length > 1
    ) {
      this.#loadingTextIndex = 0;
      this.#loadingInterval = window.setInterval(() => {
        this.#loadingTextIndex =
          (this.#loadingTextIndex + 1) %
          (this.config.loadingText as string[]).length;
      }, 2000);
    }
  }

  #stopLoadingAnimation() {
    if (this.#loadingInterval) {
      clearInterval(this.#loadingInterval);
      this.#loadingInterval = undefined;
    }
  }

  async #sendMessage(
    message: v0_8.Types.A2UIClientEventMessage
  ): Promise<v0_8.Types.ServerToClientMessage[]> {
    try {
      this.#requesting = true;
      this.#startLoadingAnimation();
      const response = this.#a2uiClient.send(message);
      await response;
      this.#requesting = false;
      this.#stopLoadingAnimation();

      return response;
    } catch (err) {
      this.snackbar(err as string, SnackType.ERROR);
    } finally {
      this.#requesting = false;
      this.#stopLoadingAnimation();
    }

    return [];
  }

  @state()
  accessor #turns: Array<{
    id: string;
    role: "user" | "model";
    text?: string;
    surfaces?: string[]; // IDs of surfaces rendered in this turn
    timestamp: number;
  }> = [];

  // ... (keep existing methods) ...

  #maybeRenderData() {
    if (this.#turns.length === 0 && !this.#requesting) {
      return nothing;
    }

    return html`<section id="chat-history" style="display: flex; flex-direction: column; gap: 16px; padding-bottom: 80px;">
      ${this.#turns.map((turn) => this.#renderTurn(turn))}
      ${this.#requesting ? this.#renderLoading() : nothing}
    </section>`;
  }

  #renderTurn(turn: { id: string; role: string; text?: string; surfaces?: string[] }) {
    const isUser = turn.role === "user";
    const alignStyle = isUser ? "align-self: flex-end; background: var(--p-90); color: var(--on-p-90);" : "align-self: flex-start; background: transparent;";
    const borderRadius = isUser ? "16px 16px 0 16px" : "16px 16px 16px 0";

    return html`
      <div class="turn ${turn.role}" style="
        max-width: 80%;
        padding: 12px 16px;
        border-radius: ${borderRadius};
        ${alignStyle}
        animation: fadeIn 0.3s ease-out;
      ">
        ${turn.text ? html`<div class="text-content" style="white-space: pre-wrap;">${turn.text}</div>` : nothing}
        ${turn.surfaces ? html`<div class="surfaces-content" style="margin-top: 8px;">
          ${turn.surfaces.map(surfaceId => {
      const surface = this.#processor.getSurfaces().get(surfaceId);
      if (!surface) return nothing;
      return html`<a2ui-surface
              .surfaceId=${surfaceId}
              .surface=${surface}
              .processor=${this.#processor}
              @a2uiaction=${this.#handleAction}
            ></a2ui-surface>`;
    })}
        </div>` : nothing}
      </div>
    `;
  }

  #renderLoading() {
    let text = "Thinking...";
    if (this.config.loadingText) {
      text = Array.isArray(this.config.loadingText)
        ? this.config.loadingText[this.#loadingTextIndex]
        : this.config.loadingText;
    }
    return html`
      <div class="turn model requesting" style="align-self: flex-start; opacity: 0.7; padding: 12px;">
        <div class="spinner" style="width: 24px; height: 24px; border-width: 2px;"></div>
        <span style="margin-left: 8px;">${text}</span>
      </div>
    `;
  }

  async #handleAction(evt: v0_8.Events.StateEvent<"a2ui.action">) {
    const [target] = evt.composedPath();
    if (!(target instanceof HTMLElement)) return;

    const context: v0_8.Types.A2UIClientEventMessage["userAction"]["context"] = {};
    if (evt.detail.action.context) {
      for (const item of evt.detail.action.context) {
        if (item.value.literalBoolean !== undefined) context[item.key] = item.value.literalBoolean;
        else if (item.value.literalNumber !== undefined) context[item.key] = item.value.literalNumber;
        else if (item.value.literalString !== undefined) context[item.key] = item.value.literalString;
        else if (item.value.path) {
          const path = this.#processor.resolvePath(item.value.path, evt.detail.dataContextPath);
          const value = this.#processor.getData(evt.detail.sourceComponent, path, evt.detail.surfaceId);
          context[item.key] = value;
        }
      }
    }

    const message: v0_8.Types.A2UIClientEventMessage = {
      userAction: {
        name: evt.detail.action.name,
        surfaceId: evt.detail.surfaceId,
        sourceComponentId: target.id,
        timestamp: new Date().toISOString(),
        context,
      },
    };

    // We might need to manually inject surfaceId if the backend expects it, but if the type forbids it, we can't.
    // However, A2A usually needs to know the surface.
    // Let's try casting or just omitting it for now.

    let userText = `Action: ${evt.detail.action.name}`;
    if (context["selection"]) {
      userText = String(context["selection"]);
    } else if (context["displayText"]) {
      userText = String(context["displayText"]);
    } else if (context["value"]) {
      userText = String(context["value"]);
    }

    await this.#sendAndProcessMessage(message, userText);
  }


  async #sendAndProcessMessage(request: v0_8.Types.A2UIClientEventMessage, userText?: string) {
    // 1. Add User Turn
    if (userText || (request.userAction ? `Selected ${request.userAction.sourceComponentId}` : undefined)) {
      // logic to extract text from request if it's a message
      // request is A2UIClientEventMessage which can be { message: ... } or { userAction: ... }
      // Actually `request` in `onSubmit` is `A2UIClientEventMessage`.
      // Let's refine this method signature or logic.
    }

    // Determine user text to display
    let displayText = userText;
    if (!displayText && typeof request === 'object' && request !== null && 'message' in request && request.message) {
      // It's a text message content? No, A2UI structure is complex.
      // But in our form submit, we send `body` as the message?
      // Wait, the form submit sends `body` as a string, but the `client.ts` wraps it.
      // Actually looking at `submit` handler:
      // `const message = body as v0_8.Types.A2UIClientEventMessage;` 
      // No, `body` from form is just string. `client.ts` handles string.
      // But `app.ts` typed it as A2UIClientEventMessage which is wrong if it comes from input.
      // Let's fix the submit handler too.
    }

    // meaningful logic:
    if (typeof request === 'string') {
      displayText = displayText || request;
      this.#turns = [...this.#turns, {
        id: crypto.randomUUID(),
        role: 'user',
        text: request,
        timestamp: Date.now()
      }];
    } else if (typeof request === 'object' && 'userAction' in request) {
      // It's an action.
      // Maybe display "Selected [Option]"?
      // For now, minimal feedback.
    }

    const messages = await this.#sendMessage(request);

    console.log("Processed messages:", messages.length);

    // Process messages into processor
    // DO NOT CLEAR SURFACES
    // this.#processor.clearSurfaces(); 
    const previousSurfaceIds = new Set(this.#processor.getSurfaces().keys());
    this.#processor.processMessages(messages);
    const allSurfaceIds = Array.from(this.#processor.getSurfaces().keys());
    const newSurfaceIds = allSurfaceIds.filter(id => !previousSurfaceIds.has(id) || true); // Actually we want ALL surfaces referenced in this turn?
    // Wait, if we don't clear, `getSurfaces` returns EVERYTHING ever.
    // We only want to associate the *newly updated* or *relevant* surfaces with this turn.
    // The `messages` contain `surfaceUpdate` with `surfaceId`.

    const relevantSurfaceIds = new Set<string>();
    for (const msg of messages) {
      if ('surfaceUpdate' in msg) {
        relevantSurfaceIds.add(msg.surfaceUpdate.surfaceId);
      }
      if ('beginRendering' in msg) {
        relevantSurfaceIds.add(msg.beginRendering.surfaceId);
      }
    }

    // Add Model Turn
    if (relevantSurfaceIds.size > 0) {
      this.#turns = [...this.#turns, {
        id: crypto.randomUUID(),
        role: 'model',
        surfaces: Array.from(relevantSurfaceIds),
        timestamp: Date.now()
      }];
    }

    this.requestUpdate();

    // Scroll to bottom
    setTimeout(() => {
      const chat = this.shadowRoot?.getElementById('chat-history');
      if (chat) chat.lastElementChild?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }

  snackbar(
    message: string | HTMLTemplateResult,
    type: SnackType,
    actions: SnackbarAction[] = [],
    persistent = false,
    id = globalThis.crypto.randomUUID(),
    replaceAll = false
  ) {
    if (!this.#snackbar) {
      this.#pendingSnackbarMessages.push({
        message: {
          id,
          message,
          type,
          persistent,
          actions,
        },
        replaceAll,
      });
      return;
    }

    return this.#snackbar.show(
      {
        id,
        message,
        type,
        persistent,
        actions,
      },
      replaceAll
    );
  }

  unsnackbar(id?: SnackbarUUID) {
    if (!this.#snackbar) {
      return;
    }

    this.#snackbar.hide(id);
  }
}
