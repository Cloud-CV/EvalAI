import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// import component
import { AnalyticsComponent} from './analytics.component';
import { HostAnalyticsComponent } from './host-analytics/host-analytics.component';

const routes: Routes = [
  {
    path: '',
    component: AnalyticsComponent,
    children: [
      {path: '', redirectTo: 'host-analytics', pathMatch: 'full'},
      {path: 'host-analytics', component: HostAnalyticsComponent}
    ]
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class AnalyticsRoutingModule { }
