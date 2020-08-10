import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ChallengesubmitComponent } from './challengesubmit.component';
import { ChallengeService } from '../../../services/challenge.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { GlobalService } from '../../../services/global.service';
import { ApiService } from '../../../services/api.service';
import { AuthService } from '../../../services/auth.service';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';
import { EndpointsService } from '../../../services/endpoints.service';
import { Router, Routes } from '@angular/router';
import { ChallengeparticipateComponent } from '../challengeparticipate/challengeparticipate.component';
import { NotFoundComponent } from '../../not-found/not-found.component';

const routes: Routes = [
  { path: 'challenge/:id/participate', component: ChallengeparticipateComponent },
  { path: 'challenge/:id/submit', component: ChallengesubmitComponent },
  {
    path: '404',
    component: NotFoundComponent,
  },
  {
    path: '**',
    redirectTo: '/404',
    pathMatch: 'full',
  },
];

describe('ChallengesubmitComponent', () => {
  let router: Router;
  let component: ChallengesubmitComponent;
  let fixture: ComponentFixture<ChallengesubmitComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ChallengesubmitComponent, ChallengeparticipateComponent, NotFoundComponent],
      providers: [ChallengeService, GlobalService, AuthService, ApiService, EndpointsService],
      imports: [HttpClientModule, RouterTestingModule.withRoutes(routes)],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  }));

  beforeEach(() => {
    router = TestBed.get(Router);
    fixture = TestBed.createComponent(ChallengesubmitComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.ngZone.run(() => {
      router.navigate(['/challenge/0/submit']).then(() => {
        fixture.detectChanges();
        expect(component).toBeTruthy();
      });
    });
  });
});
