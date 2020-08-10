import { TestBed, inject } from '@angular/core/testing';
import { HttpClientModule } from '@angular/common/http';
import { ApiService } from './api.service';
import { GlobalService } from './global.service';

describe('ApiService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientModule],
      providers: [ApiService, GlobalService],
    });
  });

  it('should be created', inject([ApiService], (service: ApiService) => {
    expect(service).toBeTruthy();
  }));

  /**
   * Prepare HTTP Options test
   */
  it('Prepare Headers', inject([ApiService], (service: ApiService) => {
    expect(service).toBeTruthy();
    expect(service.prepareHttpOptions(true)['Content-Type']).toBeUndefined();
    expect(service.prepareHttpOptions()['Content-Type']).toBeDefined();
  }));

  /**
   *
   * Loading Wrapper
   */
  it('Test Loading Wrapper', inject([ApiService], (service: ApiService) => {
    expect(service).toBeTruthy();
    const SPIES = {
      success: () => {},
      error: () => {},
      final: () => {},
    };
    const SPY1 = spyOn(SPIES, 'success');
    const SPY2 = spyOn(SPIES, 'error');
    const SPY3 = spyOn(SPIES, 'final');

    const HTTP_CALL_MOCK = {
      subscribe: (one, two, three) => {
        SPIES.success();
        SPIES.error();
        SPIES.final();
        one();
        two();
        three();
      },
    };
    const RET = service.loadingWrapper(HTTP_CALL_MOCK);
    RET.subscribe(null, null, null);
    expect(SPY1).toHaveBeenCalled();
    expect(SPY2).toHaveBeenCalled();
    expect(SPY3).toHaveBeenCalled();
  }));
});
