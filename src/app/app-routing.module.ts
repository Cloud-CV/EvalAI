import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { HomeComponent } from './components/home/home.component';
import { PubliclistsComponent } from './components/publiclists/publiclists.component';
import { TeamlistComponent } from './components/publiclists/teamlist/teamlist.component';
import { ContactComponent } from './components/contact/contact.component';
import { PrivacyPolicyComponent } from './components/privacy-policy/privacy-policy.component';
import { GetInvolvedComponent } from './components/get-involved/get-involved.component';
import { AboutComponent } from './components/about/about.component';
import { ChallengeCreateComponent } from './components/challenge-create/challenge-create.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { ProfileComponent } from './components/profile/profile.component';
import { OurTeamComponent } from './components/our-team/our-team.component';
import { NotFoundComponent } from './components/not-found/not-found.component';
import {AnalyticsComponent} from './components/analytics/analytics.component';
import {HostAnalyticsComponent} from './components/analytics/host-analytics/host-analytics.component';

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
