import { Component, computed, inject, OnInit, signal } from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { RouterLink } from "@angular/router";
import { ApiService } from "./api.service";
import { Dashboard, Team, Work } from "./models";

@Component({
  selector: "app-dashboard",
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: "./dashboard.component.html",
})
export class DashboardComponent implements OnInit {
  api = inject(ApiService);
  data = signal<Dashboard>({ classes: [], works: [] });
  loading = signal(true);
  busy = signal(false);
  selectedId = signal<number | null>(null);
  selected = computed(
    () => this.data().works.find((w) => w.id === this.selectedId()) ?? null,
  );
  isTeacher = computed(() => this.api.user()?.role !== "student");
  teams = computed(() => this.data().works.flatMap((w) => w.teams));
  submissions = computed(() =>
    this.teams().reduce((n, t) => n + (t.submitted ?? 0), 0),
  );
  expected = computed(() =>
    this.teams().reduce((n, t) => n + t.members.length, 0),
  );
  panel = signal<"class" | "work" | "team" | null>(null);
  classForm = { id: null as number | null, name: "" };
  workForm = {
    id: null as number | null,
    classroom_id: 0,
    title: "",
    description: "",
    deadline: "",
  };
  teamForm = {
    id: null as number | null,
    name: "",
    grade: null as number | null,
    emails: "",
  };

  ngOnInit(): void {
    void this.load();
  }

  async load(): Promise<void> {
    try {
      const data = await this.api.get<Dashboard>("/dashboard");
      this.data.set(data);
      if (!data.works.some((w) => w.id === this.selectedId()))
        this.selectedId.set(data.works[0]?.id ?? null);
    } catch (error) {
      this.api.report(error);
    } finally {
      this.loading.set(false);
    }
  }

  async action(
    path: string,
    method: string,
    payload: unknown,
    message: string,
  ): Promise<void> {
    if (this.busy()) return;
    this.busy.set(true);
    try {
      await this.api.request(path, method, payload);
      this.panel.set(null);
      this.api.success(message);
      await this.load();
    } catch (error) {
      this.api.report(error);
    } finally {
      this.busy.set(false);
    }
  }

  openClass(item?: { id: number; name: string }): void {
    this.classForm = { id: item?.id ?? null, name: item?.name ?? "" };
    this.panel.set("class");
  }

  saveClass(): void {
    void this.action(
      this.classForm.id ? `/classes/${this.classForm.id}` : "/classes",
      this.classForm.id ? "PATCH" : "POST",
      this.classForm,
      "Clase guardada.",
    );
  }

  openWork(work?: Work): void {
    const date = work
      ? new Date(work.deadline)
      : new Date(Date.now() + 7 * 86400000);
    const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
    this.workForm = {
      id: work?.id ?? null,
      classroom_id: work?.classroom_id ?? this.data().classes[0]?.id ?? 0,
      title: work?.title ?? "",
      description: work?.description ?? "",
      deadline: local,
    };
    this.panel.set("work");
  }

  saveWork(): void {
    const data = {
      ...this.workForm,
      deadline: new Date(this.workForm.deadline).toISOString(),
    };
    void this.action(
      data.id ? `/works/${data.id}` : "/works",
      data.id ? "PATCH" : "POST",
      data,
      "Trabajo guardado.",
    );
  }

  openTeam(team?: Team): void {
    this.teamForm = {
      id: team?.id ?? null,
      name: team?.name ?? "",
      grade: team?.grade ?? null,
      emails: team?.members.map((m) => m.email).join("\n") ?? "",
    };
    this.panel.set("team");
  }

  saveTeam(): void {
    const data = {
      ...this.teamForm,
      emails: this.teamForm.emails.split(/[\s,;]+/).filter(Boolean),
    };
    void this.action(
      data.id ? `/teams/${data.id}` : `/works/${this.selectedId()}/teams`,
      data.id ? "PATCH" : "POST",
      data,
      "Equipo guardado.",
    );
  }

  remove(path: string, label: string): void {
    if (
      confirm(
        `¿Eliminar ${label}? Se borrarán también sus equipos y evaluaciones, si los tiene. Esta acción no se puede deshacer.`,
      )
    ) {
      void this.action(path, "DELETE", undefined, "Registro eliminado.");
    }
  }

  state(action: string): void {
    if (
      action === "publish" &&
      !confirm(
        "¿Cerrar el trabajo y publicar las notas individuales? Cada alumno podrá ver su resultado.",
      )
    )
      return;
    void this.action(
      `/works/${this.selectedId()}/state`,
      "POST",
      { action },
      "Estado del trabajo actualizado.",
    );
  }

  async copy(team: Team): Promise<void> {
    try {
      await navigator.clipboard.writeText(team.link ?? "");
      this.api.success("Enlace del equipo copiado.");
    } catch {
      this.api.report(
        new Error(
          "No se pudo copiar. Selecciona y copia el enlace que aparece en el equipo.",
        ),
      );
    }
  }

  async invite(team: Team): Promise<void> {
    if (
      this.busy() ||
      !confirm(
        `Enviar el enlace de ${team.name} a ${team.members.length} integrantes: ${team.members.map((m) => m.email).join(", ")}. ¿Continuar?`,
      )
    )
      return;
    this.busy.set(true);
    try {
      const result = await this.api.request<{
        sent: string[];
        failed: string[];
      }>(`/teams/${team.id}/invite`, "POST", {});
      if (result.failed.length)
        this.api.report(
          new Error(
            `Enviados: ${result.sent.length}. No se pudo enviar a: ${result.failed.join(", ")}. Comprueba la configuración de correo.`,
          ),
        );
      else
        this.api.success(`Correo enviado a ${result.sent.length} integrantes.`);
    } catch (error) {
      this.api.report(error);
    } finally {
      this.busy.set(false);
    }
  }

  async export(): Promise<void> {
    if (this.busy()) return;
    this.busy.set(true);
    try {
      const response = await fetch(`/api/works/${this.selectedId()}/export`);
      if (!response.ok) throw new Error((await response.json()).error);
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `coevaluacion-trabajo-${this.selectedId()}.xlsx`;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      this.api.success("Excel descargado. Contiene información confidencial.");
    } catch (error) {
      this.api.report(error);
    } finally {
      this.busy.set(false);
    }
  }

  hasMr(team: Team): boolean {
    return team.evaluations?.some((e) => e.warnings.length > 0) ?? false;
  }

  memberName(team: Team, id: number | undefined): string {
    return team.members.find((m) => m.id === id)?.name ?? "";
  }
}
