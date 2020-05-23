import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

// import component
import { ChallengelistComponent } from './challengelist/challengelist.component';
import { PubliclistsComponent } from './publiclists.component';
import { TeamlistComponent } from './teamlist/teamlist.component';

const routes: Routes = [
  {
    path: '',
    component: PubliclistsComponent,
    children: [
      {path: '', redirectTo: 'all', pathMatch: 'full'},
      {path: 'all', component: ChallengelistComponent},
      {path: 'me', component: ChallengelistComponent}
    ]
  }
];

const teamListRoutes: Routes = [
  {
    path: '',
    component: PubliclistsComponent,
    children: [
      {path: '', redirectTo: 'participants', pathMatch: 'full'},
      {path: 'participants', component: TeamlistComponent},
      {path: 'hosts', component: TeamlistComponent}
    ]
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PubliclistRoutingModule {}

@NgModule({
  imports: [RouterModule.forChild(teamListRoutes)],
  exports: [RouterModule]
})
export class TeamlistsRoutingModule { }
