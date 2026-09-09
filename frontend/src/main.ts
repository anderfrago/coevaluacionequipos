import { bootstrapApplication } from "@angular/platform-browser";
import { registerLocaleData } from "@angular/common";
import localeEs from "@angular/common/locales/es";
import { LOCALE_ID } from "@angular/core";
import { provideRouter } from "@angular/router";
import { AppComponent } from "./app/app.component";
import { DashboardComponent } from "./app/dashboard.component";
import { EvaluationComponent } from "./app/evaluation.component";
import { UsersComponent } from "./app/users.component";

registerLocaleData(localeEs);

bootstrapApplication(AppComponent, {
  providers: [
    { provide: LOCALE_ID, useValue: "es" },
    provideRouter([
      { path: "", component: DashboardComponent },
      { path: "evaluar/:token", component: EvaluationComponent },
      { path: "usuarios", component: UsersComponent },
      { path: "**", redirectTo: "" },
    ]),
  ],
}).catch(console.error);
