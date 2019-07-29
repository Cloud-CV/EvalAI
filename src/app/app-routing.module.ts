import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';
import { HomeComponent } from './components/home/home.component';
import { AuthComponent } from './components/auth/auth.component';
import { LoginComponent } from './components/auth/login/login.component';
import { SignupComponent } from './components/auth/signup/signup.component';
import { VerifyEmailComponent } from './components/auth/verify-email/verify-email.component';
import { PubliclistsComponent } from './components/publiclists/publiclists.component';
import { ChallengelistComponent } from './components/publiclists/challengelist/challengelist.component';
import { TeamlistComponent } from './components/publiclists/teamlist/teamlist.component';
import { ContactComponent } from './components/contact/contact.component';
import { PrivacyPolicyComponent } from './components/privacy-policy/privacy-policy.component';
import { GetInvolvedComponent } from './components/get-involved/get-involved.component';
import { AboutComponent } from './components/about/about.component';
import { ChallengeComponent } from './components/challenge/challenge.component';
import { ChallengesettingsComponent } from './components/challenge/challengesettings/challengesettings.component';
import { ChallengeoverviewComponent} from './components/challenge/challengeoverview/challengeoverview.component';
import { ChallengeevaluationComponent } from './components/challenge/challengeevaluation/challengeevaluation.component';
import { ChallengephasesComponent} from './components/challenge/challengephases/challengephases.component';
import { ChallengeparticipateComponent } from './components/challenge/challengeparticipate/challengeparticipate.component';
import { ChallengeleaderboardComponent } from './components/challenge/challengeleaderboard/challengeleaderboard.component';
import { ChallengesubmitComponent } from './components/challenge/challengesubmit/challengesubmit.component';
import { ChallengesubmissionsComponent } from './components/challenge/challengesubmissions/challengesubmissions.component';
import {
  ChallengeviewallsubmissionsComponent
} from './components/challenge/challengeviewallsubmissions/challengeviewallsubmissions.component';
import { ChallengeCreateComponent } from './components/challenge-create/challenge-create.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ProfileComponent } from './components/profile/profile.component';
import { OurTeamComponent } from './components/our-team/our-team.component';
import { NotFoundComponent } from './components/not-found/not-found.component';
import {AnalyticsComponent} from './components/analytics/analytics.component';
import {HostAnalyticsComponent} from './components/analytics/host-analytics/host-analytics.component';
import {ResetPasswordComponent} from './components/auth/reset-password/reset-password.component';
import {ResetPasswordConfirmComponent} from './components/auth/reset-password-confirm/reset-password-confirm.component';

const routes: Routes = [
  {
    path: '',
    component: HomeComponent,
    data: {
      'title': 'EvalAI - Welcome'
    }
  },
  {
    path: 'about',
    component: AboutComponent
  },
  {
    path: 'auth',
    component: AuthComponent,
    children: [
      {path: '', redirectTo: 'login', pathMatch: 'full'},
      {path: 'login', component: LoginComponent},
      {path: 'reset-password', component: ResetPasswordComponent},
      {path: 'reset-password/confirm/:user_id/:reset_token', component: ResetPasswordConfirmComponent},
      {path: 'signup', component: SignupComponent},
      {path: 'verify-email/:token', component: VerifyEmailComponent},
      {path: '**', redirectTo: 'login'}
    ]
  },
  {
    path: 'challenge',
    redirectTo: 'challenges'
  },
  {
    path: 'challenge/:id',
    component: ChallengeComponent,
    children: [
      {path: '', redirectTo: 'overview', pathMatch: 'full'},
      {path: 'overview', component: ChallengeoverviewComponent},
      {path: 'evaluation', component: ChallengeevaluationComponent},
      {path: 'phases', component: ChallengephasesComponent},
      {path: 'participate', component: ChallengeparticipateComponent},
      {path: 'submit', component: ChallengesubmitComponent},
      {path: 'my-submissions', component: ChallengesubmissionsComponent},
      {path: 'my-submissions/:phase', component: ChallengesubmissionsComponent},
      {path: 'mysubmissions/:phase/:submission', component: ChallengesubmissionsComponent},
      {path: 'view-all-submissions', component: ChallengeviewallsubmissionsComponent},
      {path: 'leaderboard', component: ChallengeleaderboardComponent},
      {path: 'leaderboard/:split', component: ChallengeleaderboardComponent},
      {path: 'leaderboard/:split/:entry', component: ChallengeleaderboardComponent},
      {path: 'settings', component: ChallengesettingsComponent}
    ]
  },
  {
    path: 'challenges',
    component: PubliclistsComponent,
    children: [
      {path: '', redirectTo: 'all', pathMatch: 'full'},
      {path: 'all', component: ChallengelistComponent},
      {path: 'me', component: ChallengelistComponent}
    ]
  },
  {
    path: 'challenge-create',
    component: ChallengeCreateComponent
  },
  {
    path: 'contact',
    component: ContactComponent
  },
  {
    path: 'dashboard',
    component: DashboardComponent,
  },
  {
    path: 'analytics',
    component: AnalyticsComponent,
    children: [
      {path: '', redirectTo: 'host-analytics', pathMatch: 'full'},
      {path: 'host-analytics', component: HostAnalyticsComponent}
    ]
  },
  {
    path: 'get-involved',
    component: GetInvolvedComponent
  },
  {
    path: 'our-team',
    component: OurTeamComponent
  },
  {
    path: 'privacy-policy',
    component: PrivacyPolicyComponent
  },
  {
    path: 'profile',
    component: ProfileComponent
  },
  {
    path: 'teams',
    component: PubliclistsComponent,
    children: [
      {path: '', redirectTo: 'participants', pathMatch: 'full'},
      {path: 'participants', component: TeamlistComponent},
      {path: 'hosts', component: TeamlistComponent}
    ]
  },
  {
    path: '404',
    component: NotFoundComponent
  },
  {
    path: '**',
    redirectTo: '/404',
    pathMatch: 'full'
  }
];

@NgModule({
  imports: [ RouterModule.forRoot(routes) ],
  exports: [ RouterModule ]
})
export class AppRoutingModule {}
