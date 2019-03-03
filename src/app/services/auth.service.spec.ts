import { TestBed, inject } from '@angular/core/testing';

import { AuthService } from './auth.service';
import { GlobalService } from './global.service';
import { EndpointsService } from './endpoints.service';
import { ApiService } from './api.service';
import { HttpClientModule } from '@angular/common/http';

describe('AuthService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [AuthService, GlobalService, ApiService, EndpointsService],
      imports: [ HttpClientModule ]
    });
  });

  it('should be created', inject([AuthService], (service: AuthService) => {
    expect(service).toBeTruthy();
  }));
});
