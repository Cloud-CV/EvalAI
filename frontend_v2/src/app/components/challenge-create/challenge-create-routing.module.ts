import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// import component
import { ChallengeCreateComponent } from './challenge-create.component';

const routes: Routes = [
  {
    path: '',
    component: ChallengeCreateComponent
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ChallengeCreateRoutingModule { }
