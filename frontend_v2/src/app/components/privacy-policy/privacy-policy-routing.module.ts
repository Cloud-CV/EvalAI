import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

// import component
import { PrivacyPolicyComponent } from './privacy-policy.component';

const routes: Routes = [
  {
    path: '',
    component: PrivacyPolicyComponent,
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class PrivacyPolicyRoutingModule {}
