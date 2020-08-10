import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FeaturedChallengesComponent } from './featured-challenges.component';
import { RouterTestingModule } from '@angular/router/testing';
import { GlobalService } from '../../../services/global.service';
import { AuthService } from '../../../services/auth.service';
import { EndpointsService } from '../../../services/endpoints.service';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ApiService } from '../../../services/api.service';
import { HttpClientModule } from '@angular/common/http';

describe('FeaturedChallengesComponent', () => {
  let component: FeaturedChallengesComponent;
  let fixture: ComponentFixture<FeaturedChallengesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [FeaturedChallengesComponent],
      imports: [HttpClientModule, RouterTestingModule],
      providers: [GlobalService, AuthService, EndpointsService, ApiService],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FeaturedChallengesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
