import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// import component
import { PermissionDeniedComponent } from './permission-denied.component';


const routes: Routes = [
  {
    path: '',
    component: PermissionDeniedComponent
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class PermissionDeniedRoutingModule { }
