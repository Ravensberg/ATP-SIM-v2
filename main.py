from atptour import AtpTour
import time


def main():
    atp_tour = AtpTour()

    for i in range(1):
        st = time.time()
        atp_tour.play_a_season()
        et = time.time()
        elapsed_time = et - st
        #print(f'{i}. Execution time: {elapsed_time:.2f} seconds')


if __name__ == '__main__':
    main()
