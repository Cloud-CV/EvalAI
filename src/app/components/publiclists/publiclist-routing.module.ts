import { NgModule } from '@angular/core';

import { RouterModule, Routes } from '@angular/router';
import { ChallengelistComponent } from './challengelist/challengelist.component';
import { PubliclistsComponent } from './publiclists.component';

const routes: Routes = [
  {
    path: 'challenge',
    redirectTo: 'challenges'
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
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PubliclistRoutingModule {}
