import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';

// import module
import { PermissionDeniedRoutingModule } from './permission-denied-routing.module';
import { SharedModule } from '../../shared/shared.module';

// import component
import { PermissionDeniedComponent } from './permission-denied.component';

@NgModule({
  declarations: [PermissionDeniedComponent],
  imports: [CommonModule, PermissionDeniedRoutingModule, SharedModule],
  exports: [PermissionDeniedComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
})
export class PermissionDeniedModule {}
