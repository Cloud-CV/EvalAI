import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

// import component
import { NotFoundComponent } from './not-found.component';
import { NotFoundRoutingModule } from './not-found-routing.module';

// import module
import { SharedModule } from '../../shared/shared.module';

@NgModule({
  declarations: [NotFoundComponent],
  imports: [CommonModule, NotFoundRoutingModule, SharedModule],
  exports: [NotFoundComponent],
})
export class NotFoundModule {}
