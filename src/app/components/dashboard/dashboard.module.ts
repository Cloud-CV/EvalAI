import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

// import components
import { DashboardComponent } from './dashboard.component';
import { DashboardContentComponent } from './dashboard-content/dashboard-content.component';

// import modules
import { NavModule } from '../nav/nav.module';

@NgModule({
declarations: [
  DashboardContentComponent,
  DashboardComponent
],
imports: [
  CommonModule,
  RouterModule,
  NavModule
],
exports: [
  DashboardContentComponent,
  DashboardComponent,
  NavModule
],
schemas: [ CUSTOM_ELEMENTS_SCHEMA ],
})

export class DashboardModule {}
