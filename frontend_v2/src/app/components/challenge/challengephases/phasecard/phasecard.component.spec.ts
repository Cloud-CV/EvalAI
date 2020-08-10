import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PhasecardComponent } from './phasecard.component';
import { GlobalService } from '../../../../services/global.service';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';
import { ChallengeService } from '../../../../services/challenge.service';
import { EndpointsService } from '../../../../services/endpoints.service';
import { ApiService } from '../../../../services/api.service';
import { AuthService } from '../../../../services/auth.service';

describe('PhasecardComponent', () => {
  let component: PhasecardComponent;
  let fixture: ComponentFixture<PhasecardComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [PhasecardComponent],
      providers: [GlobalService, ChallengeService, EndpointsService, ApiService, AuthService],
      imports: [RouterTestingModule, HttpClientModule],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PhasecardComponent);
    component = fixture.componentInstance;
    component['phase'] = {
      name: 'test',
      start_date: '2018-03-13T00:00:00Z',
      end_date: '2099-12-31T00:00:00Z',
      max_submissions_per_day: 90,
      max_submissions: 100,
    };
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
