// Import Modules
import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

// Import serivces
import { AuthService } from './services/auth.service';
import { ApiService } from './services/api.service';
import { GlobalService } from './global.service';

// Import Components
import { AppComponent } from './app.component';
import { HomeComponent } from './home/home.component';
import { AppRoutingModule } from './app-routing.module';
import { HeaderStaticComponent } from './partials/nav/header-static/header-static.component';
import { PrivacyPolicyComponent } from './privacy-policy/privacy-policy.component';
import { InputComponent } from './input/input.component';
import { GetInvolvedComponent } from './get-involved/get-involved.component';
import { AboutComponent } from './about/about.component';


@NgModule({
  declarations: [
    AppComponent,
    HomeComponent,
    HeaderStaticComponent,
    PrivacyPolicyComponent,
    InputComponent,
    GetInvolvedComponent,
    AboutComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule
  ],
  providers: [
    AuthService,
    ApiService,
    GlobalService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
