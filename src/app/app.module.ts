import { BrowserModule } from '@angular/platform-browser';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import { NgModule } from '@angular/core';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { FroalaEditorModule, FroalaViewModule } from 'angular-froala-wysiwyg';
import { TextareaAutosizeModule } from 'ngx-textarea-autosize';
import { OwlDateTimeModule, OwlNativeDateTimeModule } from 'ng-pick-datetime';
import { MatSelectModule } from '@angular/material/select';
import { MatChipsModule } from '@angular/material/chips';

// Import serivces
import { AuthService } from './services/auth.service';
import { WindowService } from './services/window.service';
import { ApiService } from './services/api.service';
import { GlobalService } from './services/global.service';
import { ChallengeService } from './services/challenge.service';
import { EndpointsService } from './services/endpoints.service';


// Import Components
import { AppComponent } from './app.component';
import { HomeComponent } from './components/home/home.component';
import { AppRoutingModule } from './app-routing.module';
import { HeaderStaticComponent } from './components/nav/header-static/header-static.component';
import { ContactComponent } from './components/contact/contact.component';
import { FooterComponent } from './components/nav/footer/footer.component';
import { PrivacyPolicyComponent } from './components/privacy-policy/privacy-policy.component';
import { InputComponent } from './components/utility/input/input.component';
import { AuthComponent } from './components/auth/auth.component';
import { LoginComponent } from './components/auth/login/login.component';
import { SignupComponent } from './components/auth/signup/signup.component';
import { ToastComponent } from './components/utility/toast/toast.component';
import { GetInvolvedComponent } from './components/get-involved/get-involved.component';
import { AboutComponent } from './components/about/about.component';
import { CardlistComponent } from './components/utility/cardlist/cardlist.component';
import { ChallengecardComponent } from './components/publiclists/challengelist/challengecard/challengecard.component';
import { ChallengelistComponent } from './components/publiclists/challengelist/challengelist.component';
import { TeamcardComponent } from './components/publiclists/teamlist/teamcard/teamcard.component';
import { TeamlistComponent } from './components/publiclists/teamlist/teamlist.component';
import { PubliclistsComponent } from './components/publiclists/publiclists.component';
import { ForceloginComponent } from './components/utility/forcelogin/forcelogin.component';
import { ChallengeComponent } from './components/challenge/challenge.component';
import { ChallengeoverviewComponent } from './components/challenge/challengeoverview/challengeoverview.component';
import { ChallengeevaluationComponent } from './components/challenge/challengeevaluation/challengeevaluation.component';
import { ChallengephasesComponent } from './components/challenge/challengephases/challengephases.component';
import { ChallengeparticipateComponent } from './components/challenge/challengeparticipate/challengeparticipate.component';
import { ChallengeleaderboardComponent } from './components/challenge/challengeleaderboard/challengeleaderboard.component';
import { ChallengesubmitComponent } from './components/challenge/challengesubmit/challengesubmit.component';
import { ChallengesubmissionsComponent } from './components/challenge/challengesubmissions/challengesubmissions.component';
import { PhasecardComponent } from './components/challenge/challengephases/phasecard/phasecard.component';
import { ConfirmComponent } from './components/utility/confirm/confirm.component';
import { LoadingComponent } from './components/utility/loading/loading.component';
import { SelectphaseComponent } from './components/utility/selectphase/selectphase.component';
import { HomemainComponent } from './components/home/homemain/homemain.component';
import { ChallengeCreateComponent } from './components/challenge-create/challenge-create.component';
import { VerifyEmailComponent } from './components/auth/verify-email/verify-email.component';
import { ModalComponent } from './components/utility/modal/modal.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ProfileComponent } from './components/profile/profile.component';
import { NotFoundComponent } from './components/not-found/not-found.component';
import { OurTeamComponent } from './components/our-team/our-team.component';
import { TwitterFeedComponent } from './components/home/twitter-feed/twitter-feed.component';
import { NgxTwitterTimelineModule } from 'ngx-twitter-timeline';
import { PartnersComponent } from './components/home/partners/partners.component';
import { RulesComponent } from './components/home/rules/rules.component';
import { TestimonialsComponent } from './components/home/testimonials/testimonials.component';
import { FeaturedChallengesComponent } from './components/home/featured-challenges/featured-challenges.component';
import { EditphasemodalComponent } from './components/challenge/challengephases/editphasemodal/editphasemodal.component';
import {
  TermsAndConditionsModalComponent
} from './components/challenge/challengeparticipate/terms-and-conditions-modal/terms-and-conditions-modal.component';
import {
  ChallengeviewallsubmissionsComponent
} from './components/challenge/challengeviewallsubmissions/challengeviewallsubmissions.component';
import { SideBarComponent } from './components/utility/side-bar/side-bar.component';
import { MatMenuModule } from '@angular/material/menu';
import { MatIconModule } from '@angular/material/icon';

import { DashboardContentComponent } from './components/dashboard/dashboard-content/dashboard-content.component';
@NgModule({
  declarations: [
    AppComponent,
    HomeComponent,
    HeaderStaticComponent,
    FooterComponent,
    PrivacyPolicyComponent,
    InputComponent,
    AuthComponent,
    LoginComponent,
    SignupComponent,
    ContactComponent,
    ToastComponent,
    GetInvolvedComponent,
    AboutComponent,
    CardlistComponent,
    ChallengecardComponent,
    ChallengelistComponent,
    TeamcardComponent,
    TeamlistComponent,
    PubliclistsComponent,
    ForceloginComponent,
    ChallengeComponent,
    ChallengeoverviewComponent,
    ChallengeevaluationComponent,
    ChallengephasesComponent,
    ChallengeparticipateComponent,
    ChallengeleaderboardComponent,
    ChallengesubmitComponent,
    ChallengesubmissionsComponent,
    PhasecardComponent,
    ConfirmComponent,
    LoadingComponent,
    SelectphaseComponent,
    HomemainComponent,
    ChallengeCreateComponent,
    VerifyEmailComponent,
    ModalComponent,
    DashboardComponent,
    ProfileComponent,
    NotFoundComponent,
    OurTeamComponent,
    TwitterFeedComponent,
    PartnersComponent,
    RulesComponent,
    TestimonialsComponent,
    SideBarComponent,
    FeaturedChallengesComponent,
    DashboardContentComponent,
    EditphasemodalComponent,
    ChallengeviewallsubmissionsComponent,
    TermsAndConditionsModalComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule,
    NgxTwitterTimelineModule,
    FroalaEditorModule.forRoot(),
    FroalaViewModule.forRoot(),
    TextareaAutosizeModule,
    OwlDateTimeModule,
    OwlNativeDateTimeModule,
    MatSelectModule,
    MatChipsModule,
    MatMenuModule,
    MatIconModule
  ],
  providers: [
    AuthService,
    WindowService,
    ApiService,
    GlobalService,
    ChallengeService,
    EndpointsService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
