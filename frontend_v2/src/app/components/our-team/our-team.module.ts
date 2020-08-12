import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

// import component
import { OurTeamComponent } from './our-team.component';

// import module
import { OurTeamRoutingModule } from './our-team-routing.module';
import { SharedModule } from '../../shared/shared.module';

@NgModule({
  declarations: [OurTeamComponent],
  imports: [CommonModule, OurTeamRoutingModule, SharedModule],
  exports: [OurTeamComponent],
})
export class OurTeamModule {}
