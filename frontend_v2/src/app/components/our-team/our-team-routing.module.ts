import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// import component
import { OurTeamComponent } from './our-team.component';

const routes: Routes = [
  {
    path: '',
    component: OurTeamComponent,
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class OurTeamRoutingModule {}
