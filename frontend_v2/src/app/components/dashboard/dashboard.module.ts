import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';

// import components
import { DashboardComponent } from './dashboard.component';
import { DashboardContentComponent } from './dashboard-content/dashboard-content.component';

// import modules
import { DashboardRoutingModule } from './dashboard-routing.module';
import { SharedModule } from '../../shared/shared.module';

@NgModule({
declarations: [
  DashboardContentComponent,
  DashboardComponent
],
imports: [
  CommonModule,
  DashboardRoutingModule,
  SharedModule
],
exports: [
  DashboardContentComponent,
  DashboardComponent
],
schemas: [ CUSTOM_ELEMENTS_SCHEMA ],
})

export class DashboardModule {}
