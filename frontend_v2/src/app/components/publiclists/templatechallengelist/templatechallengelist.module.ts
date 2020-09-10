import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

// import component
import { TemplateChallengeListComponent } from './templatechallengelist.component';

// import module
import { SharedModule } from '../../../shared/shared.module';

@NgModule({
  declarations: [TemplateChallengeListComponent],
  imports: [CommonModule, SharedModule],
  exports: [TemplateChallengeListComponent],
})
export class TemplateChallengeListModule {}
