import { TestBed, inject } from '@angular/core/testing';

import { EndpointsService } from './endpoints.service';

describe('EndpointsService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [EndpointsService]
    });
  });

  it('should be created', inject([EndpointsService], (service: EndpointsService) => {
    expect(service).toBeTruthy();
  }));
});
