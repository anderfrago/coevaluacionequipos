import { Component, inject, OnInit } from "@angular/core";
import { RouterLink, RouterOutlet } from "@angular/router";
import { ApiService } from "./api.service";

@Component({
  selector: "app-root",
  imports: [RouterLink, RouterOutlet],
  templateUrl: "./app.component.html",
})
export class AppComponent implements OnInit {
  api = inject(ApiService);
  loginUrl = "/auth/google?next=" + encodeURIComponent(location.pathname);
  authError = new URLSearchParams(location.search).get("auth_error");

  ngOnInit(): void {
    void this.api.session();
  }
}
