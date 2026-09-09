import { Component, computed, inject, OnInit, signal } from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormsModule } from "@angular/forms";
import { ActivatedRoute, RouterLink } from "@angular/router";
import { ApiService } from "./api.service";
import { Team, Work } from "./models";

@Component({
  selector: "app-evaluation",
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: "./evaluation.component.html",
})
export class EvaluationComponent implements OnInit {
  api = inject(ApiService);
  route = inject(ActivatedRoute);
  team = signal<Team | null>(null);
  work = signal<Work | null>(null);
  allocations = signal<Record<string, number>>({});
  comment = "";
  busy = signal(false);
  loading = signal(true);
  saved = signal(false);
  token = this.route.snapshot.paramMap.get("token") ?? "";
  total = computed(() =>
    Object.values(this.allocations()).reduce((a, b) => a + (Number(b) || 0), 0),
  );
  remaining = computed(() => (this.team()?.budget ?? 0) - this.total());
  locked = computed(
    () =>
      !!(this.work()?.closed || this.work()?.expired || this.work()?.published),
  );
  valid = computed(
    () =>
      this.remaining() === 0 &&
      Object.values(this.allocations()).every(
        (p) => Number.isInteger(p) && p >= 0 && p <= (this.team()?.budget ?? 0),
      ),
  );
  warnings = computed(() => {
    const values = Object.values(this.allocations());
    const reasons: string[] = [];
    if (values.includes(0))
      reasons.push("Has asignado 0 puntos a un integrante.");
    if (values.includes(this.team()?.budget ?? -1))
      reasons.push("Has asignado todos los puntos a una persona.");
    if (values.length && new Set(values).size === 1)
      reasons.push("Has asignado los mismos puntos a todos.");
    return reasons;
  });

  async ngOnInit(): Promise<void> {
    try {
      const data = await this.api.get<{ team: Team; work: Work }>(
        `/evaluation/${this.token}`,
      );
      this.team.set(data.team);
      this.work.set(data.work);
      this.allocations.set(
        data.team.own_evaluation?.allocations ??
          Object.fromEntries(data.team.members.map((m) => [String(m.id), 0])),
      );
      this.comment = data.team.own_evaluation?.comment ?? "";
      this.saved.set(!!data.team.own_evaluation);
    } catch (error) {
      this.api.report(error);
    } finally {
      this.loading.set(false);
    }
  }

  setPoints(id: number, value: number): void {
    this.allocations.update((points) => ({ ...points, [id]: value }));
    this.saved.set(false);
  }

  async save(): Promise<void> {
    if (!this.valid() || this.locked() || this.busy()) return;
    this.busy.set(true);
    try {
      await this.api.request(`/evaluation/${this.token}`, "PUT", {
        allocations: this.allocations(),
        comment: this.comment,
      });
      this.saved.set(true);
      this.api.success(
        "Evaluación guardada. Puedes modificarla hasta que se cierre el plazo.",
      );
    } catch (error) {
      this.api.report(error);
    } finally {
      this.busy.set(false);
    }
  }
}
