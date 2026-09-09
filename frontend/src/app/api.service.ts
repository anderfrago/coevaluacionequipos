import { Injectable, signal } from "@angular/core";
import { User } from "./models";

@Injectable({ providedIn: "root" })
export class ApiService {
  user = signal<User | null>(null);
  ready = signal(false);
  error = signal("");
  notice = signal("");
  private csrf = "";

  async session(): Promise<void> {
    try {
      const result = await this.get<{ user: User | null; csrf: string }>(
        "/session",
      );
      this.user.set(result.user);
      this.csrf = result.csrf;
      this.ready.set(true);
    } catch (error) {
      this.report(error);
    }
  }

  async get<T>(path: string): Promise<T> {
    return this.request<T>(path, "GET");
  }

  async request<T = { ok: boolean }>(
    path: string,
    method: string,
    data?: unknown,
  ): Promise<T> {
    const response = await fetch("/api" + path, {
      method,
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": this.csrf,
      },
      body: data === undefined ? undefined : JSON.stringify(data),
    });
    const result = await response
      .json()
      .catch(() => ({ error: "El servidor no responde correctamente." }));
    if (!response.ok) {
      if (response.status === 401) this.user.set(null);
      throw new Error(result.error || "No se pudo completar la operación.");
    }
    return result as T;
  }

  report(error: unknown): void {
    this.notice.set("");
    this.error.set(
      error instanceof Error ? error.message : "Se ha producido un error.",
    );
  }

  success(message: string): void {
    this.error.set("");
    this.notice.set(message);
  }

  async logout(): Promise<void> {
    try {
      await this.request("/logout", "POST");
      location.assign("/");
    } catch (error) {
      this.report(error);
    }
  }
}
