import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatTabsModule } from '@angular/material';

// import component
import { ChallengecardComponent } from './challengecard/challengecard.component';
import { ChallengelistComponent } from './challengelist.component';
import { TeamlistComponent } from '../teamlist/teamlist.component';
import { TeamcardComponent } from '../teamlist/teamcard/teamcard.component';
import { CardlistComponent } from '../../utility/cardlist/cardlist.component';

// import module
import { SharedModule } from '../../../shared/shared.module';
import { PermissionDeniedModule } from '../../permission-denied/permission-denied.module';

@NgModule({
  declarations: [
    ChallengelistComponent,
    ChallengecardComponent,
    TeamcardComponent,
    TeamlistComponent,
    CardlistComponent
  ],
  imports: [
    CommonModule,
    RouterModule,
    MatTabsModule,
    SharedModule,
    PermissionDeniedModule
  ],
  exports: [
    ChallengelistComponent,
    ChallengecardComponent,
    TeamcardComponent,
    TeamlistComponent,
    CardlistComponent
  ]
})
export class ChallengelistModule { }
