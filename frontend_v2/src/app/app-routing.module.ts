import { NgModule } from '@angular/core';
import { RouterModule, Routes, PreloadAllModules } from '@angular/router';

// import component
import { NotFoundComponent } from './components/not-found/not-found.component';

const routes: Routes = [
  {
    path: '',
    loadChildren: './components/home/home.module#HomeModule',
    data: {
      'title': 'EvalAI - Welcome'
    }
  },
  {
    path: 'about',
    loadChildren: './components/about/about.module#AboutModule',
  },
  {
    path: 'auth',
    loadChildren: './components/auth/auth.module#AuthModule',
  },
  {
    path: 'challenge',
    redirectTo: 'challenges'
  },
  {
    path: 'challenge/:id',
    loadChildren: './components/challenge/challenge.module#ChallengeModule',
  },
  {
    path: 'challenges',
    loadChildren: './components/publiclists/publiclist.module#PubliclistModule',
  },
  {
    path: 'challenge-create',
    loadChildren: './components/challenge-create/challenge-create.module#ChallengeCreateModule',
  },
  {
    path: 'contact',
    loadChildren: './components/contact/contact.module#ContactModule',
  },
  {
    path: 'analytics',
    loadChildren: './components/analytics/analytics.module#AnalyticsModule',
  },
  {
    path: 'get-involved',
    loadChildren: './components/get-involved/get-involved.module#GetInvolvedModule',
  },
  {
    path: 'our-team',
    loadChildren: './components/our-team/our-team.module#OurTeamModule',
  },
  {
    path: 'privacy-policy',
    loadChildren: './components/privacy-policy/privacy-policy.module#PrivacyPolicyModule',
  },
  {
    path: 'profile',
    loadChildren: './components/profile/profile.module#ProfileModule',
  },
  {
    path: 'teams',
    loadChildren: './components/publiclists/publiclist.module#TeamlistsModule',
  },
  {
    path: 'permission-denied',
    loadChildren: './components/permission-denied/permission-denied.module#PermissionDeniedModule'
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
