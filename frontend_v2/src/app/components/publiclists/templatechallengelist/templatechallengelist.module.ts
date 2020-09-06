import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

// import component
import { TemplatechallengelistComponent } from './templatechallengelist.component';

// import module
import { SharedModule } from '../../../shared/shared.module';

@NgModule({
  declarations: [TemplatechallengelistComponent],
  imports: [CommonModule, SharedModule],
  exports: [TemplatechallengelistComponent],
})
export class TemplatechallengelistModule {}
