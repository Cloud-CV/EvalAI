import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

// import component
import { ChallengeCreateComponent } from './challenge-create.component';

// import module
import { ChallengeCreateRoutingModule } from './challenge-create-routing.module';
import { SharedModule } from '../../shared/shared.module';

@NgModule({
  declarations: [
    ChallengeCreateComponent
  ],
  imports: [
    CommonModule,
    ChallengeCreateRoutingModule,
    SharedModule
  ],
  exports: [
    ChallengeCreateComponent
  ]
})
export class ChallengeCreateModule { }
