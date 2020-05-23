import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// import component
import { GetInvolvedComponent } from './get-involved.component';

const routes: Routes = [
  {
    path: '',
    component: GetInvolvedComponent
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class GetInvolvedRoutingModule { }
