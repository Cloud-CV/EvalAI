import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// import component
import { TemplateChallengeCreateComponent } from './template-challenge-create.component';

const routes: Routes = [
  {
    path: '',
    component: TemplateChallengeCreateComponent,
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class TemplateChallengeCreateRoutingModule {}