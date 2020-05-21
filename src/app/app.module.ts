import { BrowserModule } from '@angular/platform-browser';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import { NgModule } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { EmailValidator, FormsModule } from '@angular/forms';

// Import services
import { WindowService } from './services/window.service';
import { ApiService } from './services/api.service';
import { GlobalService } from './services/global.service';
import { ChallengeService } from './services/challenge.service';
import { EndpointsService } from './services/endpoints.service';


// Import Components
import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { ContactComponent } from './components/contact/contact.component';
import { PrivacyPolicyComponent } from './components/privacy-policy/privacy-policy.component';
import { GetInvolvedComponent } from './components/get-involved/get-involved.component';
import { AboutComponent } from './components/about/about.component';
import { ChallengeCreateComponent } from './components/challenge-create/challenge-create.component';
import { ProfileComponent } from './components/profile/profile.component';
import { NotFoundComponent } from './components/not-found/not-found.component';
import { OurTeamComponent } from './components/our-team/our-team.component';
import { NgxTwitterTimelineModule } from 'ngx-twitter-timeline';
import { AnalyticsComponent } from './components/analytics/analytics.component';
import { HostAnalyticsComponent } from './components/analytics/host-analytics/host-analytics.component';
import { AuthModule } from './components/auth/auth.module';
import { PubliclistModule } from './components/publiclists/publiclist.module';
import { HomeModule } from './components/home/home.module';
import { AuthService } from './services/auth.service';
import { ChallengeModule } from './components/challenge/challenge.module';
import { DashboardModule } from './components/dashboard/dashboard.module';

@NgModule({
  declarations: [
    AppComponent,
    PrivacyPolicyComponent,
    ContactComponent,
    GetInvolvedComponent,
    AboutComponent,
    ChallengeCreateComponent,
    ProfileComponent,
    NotFoundComponent,
    OurTeamComponent,
    AnalyticsComponent,
    HostAnalyticsComponent
  ],
  imports: [
    AuthModule,
    HomeModule,
    PubliclistModule,
    ChallengeModule,
    DashboardModule,
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule
  ],
  providers: [
    WindowService,
    AuthService,
    ApiService,
    GlobalService,
    ChallengeService,
    EndpointsService
  ],
  bootstrap: [AppComponent],
})
export class AppModule { }
