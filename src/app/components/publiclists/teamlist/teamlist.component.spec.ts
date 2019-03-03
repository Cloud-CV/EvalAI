import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { TeamlistComponent } from './teamlist.component';
import { RouterTestingModule } from '@angular/router/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ApiService } from '../../../services/api.service';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { ChallengeService } from '../../../services/challenge.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { HttpClientModule } from '@angular/common/http';


describe('TeamlistComponent', () => {
  let component: TeamlistComponent;
  let fixture: ComponentFixture<TeamlistComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TeamlistComponent ],
      providers: [ GlobalService, ApiService, AuthService, ChallengeService, EndpointsService ],
      imports: [ RouterTestingModule, HttpClientModule ],
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TeamlistComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
