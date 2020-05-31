import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

// import component
import { AnalyticsComponent } from './analytics.component';
import { HostAnalyticsComponent } from './host-analytics/host-analytics.component';

// import module
import { SharedModule } from '../../shared/shared.module';
import { AnalyticsRoutingModule } from './analytics-routing.module';

@NgModule({
  declarations: [
    AnalyticsComponent,
    HostAnalyticsComponent
  ],
  imports: [
    CommonModule,
    AnalyticsRoutingModule,
    SharedModule
  ],
  exports: [
    AnalyticsComponent,
    HostAnalyticsComponent
  ],
})
export class AnalyticsModule { }
