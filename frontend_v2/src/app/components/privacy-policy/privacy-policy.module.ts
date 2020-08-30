import { NgModule, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';

// import component
import { PrivacyPolicyComponent } from './privacy-policy.component';

// import module
import { PrivacyPolicyRoutingModule } from './privacy-policy-routing.module';
import { SharedModule } from '../../shared/shared.module';

@NgModule({
  declarations: [PrivacyPolicyComponent],
  imports: [CommonModule, PrivacyPolicyRoutingModule, SharedModule],
  exports: [PrivacyPolicyComponent],
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
})
export class PrivacyPolicyModule {}
