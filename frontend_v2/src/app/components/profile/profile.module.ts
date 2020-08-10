import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

// import component
import { ProfileComponent } from './profile.component';

// import module
import { ProfileRoutingModule } from './profile-routing.module';
import { SharedModule } from '../../shared/shared.module';

@NgModule({
  declarations: [ProfileComponent],
  imports: [CommonModule, ProfileRoutingModule, SharedModule],
  exports: [ProfileComponent],
})
export class ProfileModule {}
