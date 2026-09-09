import { Component, inject, OnInit, signal } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { ApiService } from "./api.service";
import { User } from "./models";

@Component({
  selector: "app-users",
  imports: [FormsModule],
  templateUrl: "./users.component.html",
})
export class UsersComponent implements OnInit {
  api = inject(ApiService);
  users = signal<User[]>([]);
  loading = signal(true);
  busy = signal(false);
  editing = signal(false);
  form = {
    id: null as number | null,
    name: "",
    email: "",
    role: "student",
    active: true,
  };

  ngOnInit(): void {
    if (this.api.user()?.role === "admin") void this.load();
  }

  async load(): Promise<void> {
    try {
      this.users.set((await this.api.get<{ users: User[] }>("/users")).users);
    } catch (error) {
      this.api.report(error);
    } finally {
      this.loading.set(false);
    }
  }

  edit(user?: User): void {
    this.form = {
      id: user?.id ?? null,
      name: user?.name ?? "",
      email: user?.email ?? "",
      role: user?.role ?? "student",
      active: user?.active ?? true,
    };
    this.editing.set(true);
  }

  async save(): Promise<void> {
    this.busy.set(true);
    try {
      await this.api.request(
        this.form.id ? `/users/${this.form.id}` : "/users",
        this.form.id ? "PATCH" : "POST",
        this.form,
      );
      this.editing.set(false);
      await this.load();
      this.api.success("Usuario guardado.");
    } catch (error) {
      this.api.report(error);
    } finally {
      this.busy.set(false);
    }
  }

  async remove(user: User): Promise<void> {
    if (
      !confirm(
        `¿Eliminar a ${user.name} (${user.email})? Si tiene historial, deberás desactivarlo en lugar de eliminarlo.`,
      )
    )
      return;
    this.busy.set(true);
    try {
      await this.api.request(`/users/${user.id}`, "DELETE");
      await this.load();
      this.api.success("Usuario eliminado.");
    } catch (error) {
      this.api.report(error);
    } finally {
      this.busy.set(false);
    }
  }
}
