import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

// import component
import { AboutComponent } from './about.component';
import { AboutRoutingModule } from './about-routing.module';

// import module
import { SharedModule } from '../../shared/shared.module';

@NgModule({
  declarations: [AboutComponent],
  imports: [CommonModule, AboutRoutingModule, SharedModule],
  exports: [AboutComponent],
})
export class AboutModule {}
